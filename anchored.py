"""OCR-anchored pipeline for energy bill extraction"""
from __future__ import annotations

import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from config import settings

# Import OCR anchor modules
from ocr_anchors.ocr_detector import OCRDetector
from ocr_anchors.anchor_detector import AnchorDetector
from ocr_anchors.crop_generator import CropGenerator
from ocr_anchors.field_extractors import FieldExtractorPrompts
from ocr_anchors.tiling_fallback import TilingFallback
from ocr_anchors.vlm_inference import infer_field

# Import existing modules for customer/consumption (keep YOLO)
import sys
sys.path.insert(0, str(Path(__file__).parent))
try:
    from detectors.object_detection import ObjectDetection
    _HAS_OBJECT_DETECTION = True
except ImportError:
    _HAS_OBJECT_DETECTION = False

# Import shared utilities
import io
import json
import re
from typing import Any

def _load_image(raw: bytes) -> Image.Image:
    """Load image from bytes"""
    return Image.open(io.BytesIO(raw)).convert("RGB")

def _read_customer_address_prompt(concessionaria: str = "", uf: str = "") -> str:
    """Load customer address prompt"""
    base_path = Path(settings.prompts_dir) / "customer_address.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")
    return base_path.read_text(encoding="utf-8").strip()

def _read_consumption_prompt() -> str:
    """Load consumption prompt"""
    path = Path(settings.prompts_dir) / "consumption.md"
    if not path.exists():
        raise RuntimeError(f"Arquivo {path.as_posix()} não encontrado.")
    return path.read_text(encoding="utf-8").strip()

def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from text"""
    text = text.strip()
    
    # Try to find JSON object
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        json_str = m.group(0)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Nenhum JSON encontrado. Texto: {text[:500]}")

# Import shared functions from main.py
import importlib.util
main_spec = importlib.util.spec_from_file_location("main", Path(__file__).parent / "main.py")
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
_ensure_contract = main_module._ensure_contract
_infer_one_full = main_module._infer_one  # For full image inference
_read_prompt = main_module._read_prompt  # For reading concession-specific prompts

app = FastAPI(title="Energy Extractor (OCR-Anchored Pipeline)")

def log_main(msg: str) -> None:
    """Log message"""
    print(msg, flush=True)

# Global OCR components (lazy loaded)
_OCR_DETECTOR: Optional[OCRDetector] = None
_ANCHOR_DETECTOR: Optional[AnchorDetector] = None
_CROP_GENERATOR: Optional[CropGenerator] = None
_TILING_FALLBACK: Optional[TilingFallback] = None
_OBJECT_DETECTOR: Optional[ObjectDetection] = None


def get_ocr_detector() -> Optional[OCRDetector]:
    """Get or create OCR detector (singleton)
    
    NOTA: OCR detector não é mais usado por padrão - muito lento.
    Mantido apenas para uso futuro/experimental.
    
    Returns:
        OCRDetector instance or None if unavailable
    """
    # Desabilitado - não inicializar OCR por padrão (muito lento)
    return None
    
    # Código abaixo não é executado (mantido para referência futura)
    global _OCR_DETECTOR
    if _OCR_DETECTOR is None:
        try:
            _OCR_DETECTOR = OCRDetector(lang="pt")
            log_main("[ocr_anchors] OCR detector inicializado")
        except (RuntimeError, ImportError, OSError, Exception) as e:
            log_main(f"[ocr_anchors] AVISO: OCR não disponível: {e}")
            _OCR_DETECTOR = None
    return _OCR_DETECTOR


def get_anchor_detector() -> AnchorDetector:
    """Get or create anchor detector (singleton)"""
    global _ANCHOR_DETECTOR
    if _ANCHOR_DETECTOR is None:
        _ANCHOR_DETECTOR = AnchorDetector(case_sensitive=False)
    return _ANCHOR_DETECTOR


def get_crop_generator() -> CropGenerator:
    """Get or create crop generator (singleton)"""
    global _CROP_GENERATOR
    if _CROP_GENERATOR is None:
        _CROP_GENERATOR = CropGenerator(
            padding_x=50,
            padding_y=30,
            min_crop_size=(100, 50),
            max_crop_size=(800, 400)
        )
    return _CROP_GENERATOR


def get_tiling_fallback() -> TilingFallback:
    """Get or create tiling fallback (singleton)"""
    global _TILING_FALLBACK
    if _TILING_FALLBACK is None:
        _TILING_FALLBACK = TilingFallback(
            tile_size=(400, 400),
            overlap=50
        )
    return _TILING_FALLBACK


def get_object_detector() -> Optional[ObjectDetection]:
    """Get or create object detector (singleton)"""
    global _OBJECT_DETECTOR
    if _HAS_OBJECT_DETECTION and _OBJECT_DETECTOR is None:
        try:
            _OBJECT_DETECTOR = ObjectDetection()
            log_main("[ocr_anchors] Object detector inicializado")
        except Exception as e:
            log_main(f"[ocr_anchors] erro ao inicializar object detector: {e}")
    return _OBJECT_DETECTOR


async def extract_fields_via_anchors(
    img: Image.Image,
    fields: list[str]
) -> Dict[str, Any]:
    """Extract fields using OCR anchor detection
    
    Args:
        img: Full bill image
        fields: List of field names to extract
        
    Returns:
        Dict with extracted field values
    """
    results = {}
    
    # Step 1: Run OCR to get text boxes (usando mesma config do ocr.py)
    log_main("[ocr_anchors] executando OCR...")
    t_ocr_start = time.time()
    ocr_detector = get_ocr_detector()
    
    if ocr_detector is None:
        log_main("[ocr_anchors] OCR não disponível, pulando detecção de âncoras")
        return results
    
    ocr_results = []
    ocr_time_ms = 0.0
    try:
        ocr_results = ocr_detector.detect_text_boxes(img)
        t_ocr_end = time.time()
        ocr_time_ms = (t_ocr_end - t_ocr_start) * 1000
        log_main(f"[ocr_anchors] OCR concluído: {len(ocr_results)} textos encontrados em {ocr_time_ms:.1f}ms")
        
        # Log first few texts for debugging
        if ocr_results:
            sample_texts = [r['text'][:50] for r in ocr_results[:5]]
            log_main(f"[ocr_anchors] Exemplos de textos encontrados: {sample_texts}")
    except Exception as e:
        log_main(f"[ocr_anchors] Erro ao executar OCR: {e}")
        return results
    
    if not ocr_results:
        log_main("[ocr_anchors] AVISO: Nenhum texto detectado pelo OCR")
        return results
    
    # OCR pode ser lento, mas se já rodou e encontrou textos, vamos usar
    # O trabalho pesado já foi feito, então vale a pena usar os resultados
    
    # Step 2: Find anchors for each field
    anchor_detector = get_anchor_detector()
    crop_generator = get_crop_generator()
    img_width, img_height = img.size
    
    anchors_found = []
    for field in fields:
        anchor = anchor_detector.find_best_anchor(ocr_results, field, img_width, img_height)
        if anchor:
            anchors_found.append({
                'field': field,
                'bbox': anchor['bbox'],
                'text': anchor['text'],
                'score': anchor['score']
            })
            log_main(f"[ocr_anchors] âncora encontrada para {field}: '{anchor['text']}' (score: {anchor['score']:.2f})")
        else:
            log_main(f"[ocr_anchors] âncora NÃO encontrada para {field}")
    
    # Step 3: Generate crops and extract fields
    crops = crop_generator.generate_multiple_crops(img, anchors_found)
    
    # Step 4: Run VLM on each crop
    extraction_tasks = []
    for field in fields:
        if field in crops and crops[field] is not None:
            prompt = FieldExtractorPrompts.get_prompt(field)
            if prompt:
                extraction_tasks.append((field, crops[field], prompt))
            else:
                log_main(f"[ocr_anchors] prompt não encontrado para {field}")
    
    # Run extractions in parallel (limited concurrency)
    semaphore = asyncio.Semaphore(settings.max_concurrency)
    
    async def extract_with_semaphore(field: str, crop: Image.Image, prompt: str):
        async with semaphore:
            return await infer_field(crop, prompt, field)
    
    t_extract_start = time.time()
    extraction_results = await asyncio.gather(*[
        extract_with_semaphore(field, crop, prompt)
        for field, crop, prompt in extraction_tasks
    ])
    t_extract_end = time.time()
    log_main(f"[ocr_anchors] extrações concluídas em {(t_extract_end - t_extract_start)*1000:.1f}ms")
    
    # Merge results
    for (field, _, _), result in zip(extraction_tasks, extraction_results):
        if result:
            results.update(result)
        else:
            log_main(f"[ocr_anchors] extração falhou para {field}")
    
    return results


async def extract_fields_via_tiling_fallback(
    img: Image.Image,
    missing_fields: list[str]
) -> Dict[str, Any]:
    """Fallback: extract missing fields using tiling
    
    Args:
        img: Full bill image
        missing_fields: List of fields that weren't found via anchors
        
    Returns:
        Dict with extracted field values
    """
    if not missing_fields:
        return {}
    
    log_main(f"[ocr_anchors] usando fallback tiling para: {missing_fields}")
    tiling = get_tiling_fallback()
    # Reduzir tiles de 9 para 4 (2x2) - mais rápido
    tiles = tiling.generate_adaptive_tiles(img, max_tiles=4)
    log_main(f"[ocr_anchors] gerados {len(tiles)} tiles")
    
    results = {}
    semaphore = asyncio.Semaphore(settings.max_concurrency)
    
    async def extract_from_tile(field: str, tile: Image.Image, prompt: str, tile_pos: Tuple[int, int]):
        async with semaphore:
            result = await infer_field(tile, prompt, field)
            return field, result, tile_pos
    
    # Processar todos os campos em paralelo nos tiles (mais eficiente)
    tasks = []
    for field in missing_fields:
        prompt = FieldExtractorPrompts.get_prompt(field)
        if not prompt:
            continue
        for tile, tile_pos in tiles:
            tasks.append(extract_from_tile(field, tile, prompt, tile_pos))
    
    # Executar todas as tarefas em paralelo
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Processar resultados - parar no primeiro match por campo
    found_fields = set()
    for result in all_results:
        if isinstance(result, Exception):
            continue
        field, data, tile_pos = result
        if field in found_fields:
            continue
        if data and data.get(field):
            results.update(data)
            log_main(f"[ocr_anchors] {field} encontrado no tile {tile_pos}")
            found_fields.add(field)
    
    for field in missing_fields:
        if field not in found_fields:
            log_main(f"[ocr_anchors] {field} não encontrado em nenhum tile")
    
    return results


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "pipeline": "ocr_anchored",
        "model": settings.model_id,
    }


@app.post("/extract/energy")
async def extract_energy(
    concessionaria: str = Form(...),
    uf: str = Form(...),
    file: UploadFile = File(...),
):
    """Extract energy bill data - usa pipeline YOLO + full-image (mesmo do main.py)
    
    NOTA: Pipeline OCR-anchored foi desabilitado por ser muito lento (47s+).
    Este endpoint agora usa a mesma estratégia do main.py: YOLO crops + full-image inference.
    """
    t_request_start = time.time()
    log_main(f"[req] requisição recebida (OCR-anchored): concessionaria={concessionaria}, uf={uf}")
    
    if not concessionaria.strip() or not uf.strip():
        raise HTTPException(status_code=400, detail="concessionaria e uf são obrigatórios")
    
    if file.content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(status_code=400, detail=f"content-type não suportado: {file.content_type}")
    
    raw = await file.read()
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"imagem acima do limite de {settings.max_image_mb}MB")
    
    t_start = time.time()
    img = None
    
    try:
        img = _load_image(raw)
        del raw
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"falha ao abrir imagem: {e}")
    
    # Initialize result payload
    payload = {}
    
    # OCR-ANCHORED PIPELINE COMPLETAMENTE DESABILITADO - muito lento para produção (47s+)
    # Pipeline original (YOLO + full-image) é muito mais rápido e eficiente
    
    # Step 3: Use YOLO for customer address and consumption (keep existing logic)
    customer_crop_img = None
    consumption_crop_img = None
    
    if _HAS_OBJECT_DETECTION:
        detector = get_object_detector()
        if detector:
            try:
                import tempfile
                temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img.save(temp_path.name, format='PNG')
                
                customer_crop_path = detector.detect_and_crop_customer_data(temp_path.name)
                if customer_crop_path:
                    customer_crop_img = Image.open(customer_crop_path).convert("RGB")
                
                consumption_crop_path = detector.detect_and_crop_consumption(temp_path.name)
                if consumption_crop_path:
                    consumption_crop_img = Image.open(consumption_crop_path).convert("RGB")
                
                import os
                try:
                    os.unlink(temp_path.name)
                except Exception:
                    pass
            except Exception as e:
                log_main(f"[ocr_anchors] erro ao usar YOLO: {e}")
    
    # Extract customer address (using YOLO crop)
    if customer_crop_img:
        try:
            prompt_customer = _read_customer_address_prompt(concessionaria, uf)
            result_customer = await _infer_one_full(customer_crop_img, prompt_customer)
            payload_customer = _extract_json(result_customer)
            # Merge address fields
            for key in ["rua", "numero", "complemento", "bairro", "cidade", "estado", "cep"]:
                if key in payload_customer:
                    payload[key] = payload_customer[key]
        except Exception as e:
            log_main(f"[ocr_anchors] erro ao extrair endereço: {e}")
    
    # Extract consumption (using YOLO crop)
    payload_consumption = None
    if consumption_crop_img:
        try:
            t_consumption_start = time.time()
            prompt_consumption = _read_consumption_prompt()
            log_main(f"[ocr_anchors] extraindo consumo do crop YOLO...")
            result_consumption = await _infer_one_full(consumption_crop_img, prompt_consumption)
            t_consumption_end = time.time()
            log_main(f"[ocr_anchors] inferência consumo concluída em {(t_consumption_end - t_consumption_start)*1000:.1f}ms")
            
            payload_consumption = _extract_json(result_consumption)
            log_main(f"[ocr_anchors] payload_consumption keys: {list(payload_consumption.keys()) if payload_consumption else 'None'}")
            
            if payload_consumption and 'consumo_lista' in payload_consumption:
                consumo_crop = payload_consumption['consumo_lista']
                log_main(f"[ocr_anchors] consumo_crop type: {type(consumo_crop)}, value: {consumo_crop}")
                if isinstance(consumo_crop, list) and len(consumo_crop) > 0:
                    payload['consumo_lista'] = consumo_crop
                    log_main(f"[ocr_anchors] consumo extraído do crop: {len(consumo_crop)} itens")
                else:
                    log_main(f"[ocr_anchors] AVISO: consumo_lista vazio no crop (type: {type(consumo_crop)}, len: {len(consumo_crop) if isinstance(consumo_crop, list) else 'N/A'})")
            else:
                log_main(f"[ocr_anchors] AVISO: consumo_lista não encontrado no crop. payload_consumption: {payload_consumption}")
        except Exception as e:
            log_main(f"[ocr_anchors] erro ao extrair consumo: {e}")
            import traceback
            log_main(f"[ocr_anchors] traceback: {traceback.format_exc()}")
    else:
        log_main(f"[ocr_anchors] AVISO: crop de consumo não disponível (YOLO não detectou)")
    
    # Step 4: Use full image inference for remaining fields
    # Fields that need full context or weren't found via anchors
    # NOTA: consumo_lista NÃO está aqui - deve vir do YOLO crop acima
    remaining_fields_needed = [
        'vencimento', 'mes_referencia', 'valor_fatura', 'aliquota_icms',
        'cod_cliente', 'num_instalacao', 'classificacao', 'tipo_instalacao', 
        'tensao_nominal', 'nome_cliente', 'valores_em_aberto', 'faturas_venc',
        'baixa_renda', 'tarifa_branca', 'ths_verde',
        'energia_ativa_injetada', 'energia_reativa',
        'orgao_publico', 'parcelamentos', 'alta_tensao',
    ]
    
    # Check which fields are still missing
    missing_remaining = [f for f in remaining_fields_needed if f not in payload or not payload.get(f)]
    
    # Se consumo_lista não foi extraído do crop, tenta do full-image como fallback
    if not payload.get('consumo_lista'):
        log_main("[ocr_anchors] consumo_lista não encontrado no crop, tentando full-image como fallback")
        remaining_fields_needed.append('consumo_lista')
        if 'consumo_lista' not in missing_remaining:
            missing_remaining.append('consumo_lista')
    
    if missing_remaining:
        # Resize image if too large (same logic as main.py)
        img_for_inference = img
        w, h = img.size
        pixels = w * h
        if pixels > settings.max_pixels:
            scale = (settings.max_pixels / float(pixels)) ** 0.5
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            img_for_inference = img.resize((nw, nh), Image.LANCZOS)
            log_main(f"[ocr_anchors] imagem redimensionada: {w}x{h} -> {nw}x{nh} ({pixels:,} -> {nw*nh:,} pixels)")
        
        # Use full image inference with base prompt for remaining fields
        try:
            t_full_start = time.time()
            prompt_full = _read_prompt(concessionaria, uf)
            log_main(f"[ocr_anchors] extraindo {len(missing_remaining)} campos do full-image...")
            result_full = await _infer_one_full(img_for_inference, prompt_full)
            t_full_end = time.time()
            log_main(f"[ocr_anchors] full-image inference concluída em {(t_full_end - t_full_start)*1000:.1f}ms")
            
            payload_full = _extract_json(result_full)
            log_main(f"[ocr_anchors] payload_full tem consumo_lista: {'consumo_lista' in payload_full if payload_full else False}")
            if payload_full and 'consumo_lista' in payload_full:
                consumo_full = payload_full['consumo_lista']
                log_main(f"[ocr_anchors] consumo_full do full-image: type={type(consumo_full)}, len={len(consumo_full) if isinstance(consumo_full, list) else 'N/A'}")
            
            # Merge remaining fields (don't overwrite existing fields)
            for key in missing_remaining:
                if key in payload_full:
                    # Para consumo_lista, mescla inteligentemente (mesma lógica do main.py)
                    if key == 'consumo_lista':
                        consumo_crop = payload_consumption.get('consumo_lista', []) if payload_consumption else []
                        consumo_full = payload_full.get('consumo_lista', [])
                        
                        # Mescla: usa crop se tiver mais itens, senão usa full
                        if isinstance(consumo_crop, list) and len(consumo_crop) > 0:
                            if not consumo_full or not isinstance(consumo_full, list) or len(consumo_full) == 0:
                                payload[key] = consumo_crop
                            elif len(consumo_crop) > len(consumo_full):
                                payload[key] = consumo_crop
                            else:
                                payload[key] = consumo_full
                        elif consumo_full:
                            payload[key] = consumo_full
                    elif payload_full[key]:  # Para outros campos, só se não vazio
                        payload[key] = payload_full[key]
            
            # Mescla consumo do crop após full-image (mesma lógica do main.py)
            if payload_consumption and "consumo_lista" in payload_consumption:
                consumo_crop = payload_consumption["consumo_lista"]
                consumo_full = payload.get("consumo_lista", [])
                
                if isinstance(consumo_crop, list) and len(consumo_crop) > 0:
                    if not consumo_full or not isinstance(consumo_full, list) or len(consumo_full) == 0:
                        payload["consumo_lista"] = consumo_crop
                    elif len(consumo_crop) > len(consumo_full):
                        payload["consumo_lista"] = consumo_crop
        except Exception as e:
            log_main(f"[ocr_anchors] erro ao extrair campos restantes: {e}")
    
    # Step 5: Validate and ensure contract format
    payload = _ensure_contract(payload, concessionaria, uf)
    
    t_end = time.time()
    log_main(f"[req] processamento concluído em {(t_end - t_request_start)*1000:.1f}ms")
    
    return JSONResponse(content=payload)
