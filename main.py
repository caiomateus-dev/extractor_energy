from __future__ import annotations

import asyncio
import gc
import io
import json
import os
import sys
import time
import tempfile
import threading
import fcntl
from pathlib import Path
from importlib.util import find_spec
from typing import Any, Dict, Optional, Tuple
import re

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from config import settings

# Importa detecção de objetos para recortes
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from detectors.object_detection import ObjectDetection
    _HAS_OBJECT_DETECTION = True
except ImportError as e:
    _HAS_OBJECT_DETECTION = False
    print(f"[boot] object_detection não disponível - recortes desabilitados: {e}", flush=True)

_HAS_MLX_VLM = find_spec("mlx_vlm") is not None
if _HAS_MLX_VLM:
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config


app = FastAPI(title="Energy Extractor (MLX-VLM + Qwen2.5-VL)")

PROMPTS_DIR = Path(settings.prompts_dir).resolve()


def log(msg: str) -> None:
    print(msg, flush=True)


def _key(s: str) -> str:
    """
    Normaliza chaves vindas do input (ex: "CEMIG-D" -> "cemig-d") sem regex.
    Mantém apenas [a-z0-9] e converte separadores em "-".
    """
    s = s.strip().lower()
    out: list[str] = []
    last_sep = True
    for ch in s:
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
            last_sep = False
            continue
        if not last_sep:
            out.append("-")
            last_sep = True
    if out and out[-1] == "-":
        out.pop()
    return "".join(out)


_PROMPT_MAP_CACHE: dict[str, Any] | None = None
_PROMPT_MAP_MTIME_NS: int | None = None


def _load_prompt_map() -> dict[str, Any]:
    global _PROMPT_MAP_CACHE, _PROMPT_MAP_MTIME_NS

    path = PROMPTS_DIR / "mapper.json"
    if not path.exists():
        return {}

    st = path.stat()
    mtime_ns = getattr(st, "st_mtime_ns", None) or int(st.st_mtime * 1e9)
    if _PROMPT_MAP_CACHE is not None and _PROMPT_MAP_MTIME_NS == mtime_ns:
        return _PROMPT_MAP_CACHE

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Formato inválido em {path.as_posix()}: esperado um JSON object.")

    _PROMPT_MAP_CACHE = data
    _PROMPT_MAP_MTIME_NS = mtime_ns
    return data


def _format_bytes(n: int | None) -> str:
    if n is None:
        return "n/a"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f}{u}"
        x /= 1024
    return f"{x:.1f}{units[-1]}"


def _process_rss_bytes() -> int | None:
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(rss) if os.uname().sysname == "Darwin" else int(rss) * 1024
    except Exception:
        return None


def _system_memory_total_available_bytes() -> tuple[int | None, int | None]:
    try:
        if os.uname().sysname == "Linux":
            total = available = None
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total = int(line.split()[1]) * 1024
                    elif line.startswith("MemAvailable:"):
                        available = int(line.split()[1]) * 1024
            return total, available
    except Exception:
        pass

    try:
        if os.uname().sysname == "Darwin":
            import subprocess

            total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
            vm = subprocess.check_output(["vm_stat"], text=True)
            page_size = 4096
            m = re.search(r"page size of (\\d+) bytes", vm)
            if m:
                page_size = int(m.group(1))

            pages = {}
            for line in vm.splitlines():
                mm = re.match(r"^Pages (.+?):\\s+(\\d+)\\.$", line.strip())
                if mm:
                    pages[mm.group(1)] = int(mm.group(2))

            available_pages = (
                pages.get("free", 0)
                + pages.get("inactive", 0)
                + pages.get("speculative", 0)
            )
            available = available_pages * page_size
            return total, available
    except Exception:
        pass

    return None, None


def _metal_memory_bytes() -> Dict[str, int]:
    """Retorna dict vazio - API mlx.metal foi removida (deprecated)"""
    return {}


def _clear_metal_cache() -> None:
    """
    Limpa o cache do Metal/MLX após inferência para liberar memória GPU.
    Usa mx.clear_cache() que é a API recomendada (mx.metal.clear_cache está deprecado).
    """
    try:
        import mlx.core as mx  # type: ignore
        
        # Limpa cache usando a API recomendada (não deprecada)
        if hasattr(mx, "clear_cache"):
            try:
                mx.clear_cache()
            except Exception:
                pass
        
        # Força avaliação de arrays pendentes se o modelo estiver carregado
        # Isso ajuda a liberar memória de arrays intermediários
        global MODEL
        if MODEL is not None and hasattr(MODEL, "parameters"):
            try:
                # Avalia parâmetros do modelo para sincronizar operações
                params = MODEL.parameters()
                if isinstance(params, dict):
                    # Avalia todos os parâmetros do modelo
                    mx.eval(list(params.values()))
            except Exception:
                pass
    except Exception:
        pass


def _log_system_metrics(tag: str) -> None:
    rss = _process_rss_bytes()
    total, avail = _system_memory_total_available_bytes()
    log(
        f"{tag} rss={_format_bytes(rss)} "
        f"ram_total={_format_bytes(total)} ram_avail={_format_bytes(avail)}"
    )


MODEL = PROCESSOR = CONFIG = None
OBJECT_DETECTOR = None

if not _HAS_MLX_VLM:
    log(
        "[boot] missing dependency: mlx-vlm (module: mlx_vlm). "
        "Use the project venv (e.g. `uv sync` then `uv run uvicorn main:app --reload`) "
        f"or install it into {sys.executable}."
    )
else:
    log(f"[boot] loading model: {settings.model_id}")
    MODEL, PROCESSOR = load(settings.model_id)
    CONFIG = load_config(settings.model_id)
    log("[boot] model loaded")
    _log_system_metrics("[boot][mem]")

# Inicializa detector de objetos para recortes (lazy loading - não pré-carrega modelos)
if _HAS_OBJECT_DETECTION:
    try:
        t_yolo_start = time.time()
        OBJECT_DETECTOR = ObjectDetection()
        # Não pré-carrega modelos YOLO aqui para evitar demora no boot
        # Os modelos serão carregados na primeira requisição (lazy loading)
        t_yolo_end = time.time()
        log(f"[boot] object detector inicializado em {(t_yolo_end - t_yolo_start)*1000:.1f}ms")
    except Exception as e:
        log(f"[boot] erro ao carregar object detector: {e}")
        OBJECT_DETECTOR = None


_GATE = asyncio.Semaphore(settings.max_concurrency)

# Lock entre processos para proteger operações Metal
# Metal não suporta acesso concorrente mesmo de processos diferentes
# Usa file lock para funcionar entre múltiplos workers
_METAL_LOCK_FILE = Path("/tmp/extractor_energy_metal.lock")

class MetalLock:
    """Lock entre processos usando file lock para proteger operações Metal"""
    def __init__(self):
        self.lock_file = None
    
    def __enter__(self):
        self.lock_file = open(_METAL_LOCK_FILE, 'w')
        # Bloqueia o arquivo exclusivamente (bloqueia até conseguir)
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None


def _read_prompt(concessionaria: str, uf: str) -> str:
    base_path = PROMPTS_DIR / "base.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")

    base = base_path.read_text(encoding="utf-8").strip()

    mapper = _load_prompt_map()
    prompts = mapper.get("prompts", {}) if isinstance(mapper.get("prompts", {}), dict) else {}
    aliases = mapper.get("aliases", {}) if isinstance(mapper.get("aliases", {}), dict) else {}

    concessionaria_key = _key(concessionaria)
    aliased = aliases.get(concessionaria_key)
    if isinstance(aliased, str) and aliased.strip():
        concessionaria_key = _key(aliased)
    uf_key = _key(uf)

    spec_filename: str | None = None
    by_uf = prompts.get(concessionaria_key)
    if isinstance(by_uf, dict):
        v = by_uf.get(uf_key) or by_uf.get("*")
        if isinstance(v, str) and v.strip():
            spec_filename = v.strip()
    elif isinstance(by_uf, str) and by_uf.strip():
        spec_filename = by_uf.strip()

    spec = ""
    if spec_filename:
        spec_path = PROMPTS_DIR / spec_filename
        if not spec_path.exists():
            raise RuntimeError(
                f"Prompt mapeado não encontrado: {spec_path.as_posix()} "
                f"(concessionaria={concessionaria_key}, uf={uf_key})"
            )
        spec = spec_path.read_text(encoding="utf-8").strip()

    return base + ("\n\n" + spec if spec else "")


def _save_image_temp(img: Image.Image) -> str:
    """Salva imagem PIL em arquivo temporário para uso com modelos YOLO"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    img.save(temp_path, format='PNG')
    return temp_path


def _load_image(raw: bytes) -> Image.Image:
    """
    Carrega e processa imagem de forma eficiente em memória.
    Redimensiona AGressivamente se necessário para evitar alocações excessivas no Metal.
    
    IMPORTANTE: Imagens grandes podem causar alocações de dezenas de GB no Metal
    durante o processamento do modelo VLM. Redimensionamos ANTES de processar.
    """
    # Carrega imagem diretamente do bytes
    bio = io.BytesIO(raw)
    try:
        img = Image.open(bio).convert("RGB")
        w, h = img.size
        pixels = w * h
        
        # Log do tamanho original para debug
        if pixels > settings.max_pixels:
            log(f"[img] imagem grande detectada: {w}x{h} ({pixels:,} pixels) - redimensionando")
        
        # Redimensiona ANTES de criar cópia para economizar memória
        if pixels > settings.max_pixels:
            scale = (settings.max_pixels / float(pixels)) ** 0.5
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            log(f"[img] redimensionada para: {nw}x{nh} ({nw*nh:,} pixels)")
        
        # Cria cópia final (já redimensionada se necessário)
        img_copy = img.copy()
        img.close()  # Fecha a imagem original
    finally:
        bio.close()  # Fecha o BytesIO
    
    return img_copy


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("Nenhum JSON encontrado na resposta do modelo.")
    return json.loads(m.group(0))


def _to_float(x: Any, default: float) -> float:
    try:
        if isinstance(x, str):
            s = x.replace("R$", "").replace(" ", "")
            s = s.replace(".", "").replace(",", ".")
            return float(s)
        return float(x)
    except Exception:
        return default


def _normalize_month_reference(mes_ref: str) -> str:
    """Converte mes_referencia de formato abreviado (OUT/2025) para numérico (10/2025)"""
    if not mes_ref or not isinstance(mes_ref, str):
        return mes_ref
    
    mes_ref = mes_ref.strip().upper()
    
    # Mapeamento de meses abreviados para numéricos
    month_map = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
        "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
        "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
    }
    
    # Verifica se já está no formato numérico (MM/AAAA)
    if re.match(r'^\d{2}/\d{4}$', mes_ref):
        return mes_ref
    
    # Tenta converter formato abreviado (OUT/2025 ou OUT/25)
    parts = mes_ref.split("/")
    if len(parts) == 2:
        mes_abrev = parts[0].strip()
        ano = parts[1].strip()
        
        # Converte ano de 2 dígitos para 4 dígitos se necessário
        if len(ano) == 2:
            ano_int = int(ano)
            # Assume que anos 00-50 são 2000-2050, e 51-99 são 1951-1999
            if ano_int <= 50:
                ano = f"20{ano:02d}"
            else:
                ano = f"19{ano:02d}"
        
        # Converte mês abreviado para numérico
        if mes_abrev in month_map:
            return f"{month_map[mes_abrev]}/{ano}"
    
    # Se não conseguir converter, retorna o original
    return mes_ref


def _normalize_cep(cep: str) -> str:
    """Normaliza CEP para o formato XX.XXX-XXX"""
    if not cep or not isinstance(cep, str):
        return cep
    
    # Remove todos os caracteres não numéricos
    cep_clean = re.sub(r'[^\d]', '', cep.strip())
    
    # Verifica se tem 8 dígitos
    if len(cep_clean) == 8:
        return f"{cep_clean[:2]}.{cep_clean[2:5]}-{cep_clean[5:]}"
    
    # Se não tiver 8 dígitos, retorna o original
    return cep


def _ensure_contract(payload: Dict[str, Any], concessionaria_input: str) -> Dict[str, Any]:
    template: Dict[str, Any] = {
        "cod_cliente": "",
        "conta_contrato": "",
        "complemento": "",
        "distribuidora": "",
        "num_instalacao": "",
        "classificacao": "",
        "tipo_instalacao": "",
        "tensao_nominal": "",
        "alta_tensao": False,
        "mes_referencia": "",
        "valor_fatura": 0.0,
        "vencimento": "",
        "proximo_leitura": "",
        "aliquota_icms": None,
        "baixa_renda": False,
        "energia_ativa_injetada": False,
        "energia_reativa": False,
        "orgao_publico": False,
        "parcelamentos": False,
        "tarifa_branca": False,
        "ths_verde": False,
        "faturas_venc": False,
        "valores_em_aberto": [],
        "nome_cliente": "",
        "rua": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cidade": "",
        "estado": "",
        "cep": "",
        "consumo_lista": [],
    }

    out = dict(template)
    for k in template.keys():
        if k in payload:
            out[k] = payload[k]

    if not str(out.get("distribuidora", "")).strip():
        out["distribuidora"] = concessionaria_input

    # Normaliza mes_referencia para formato numérico
    mes_ref = str(out.get("mes_referencia", "")).strip()
    if mes_ref:
        out["mes_referencia"] = _normalize_month_reference(mes_ref)

    # Normaliza CEP para formato XX.XXX-XXX
    cep = str(out.get("cep", "")).strip()
    if cep:
        out["cep"] = _normalize_cep(cep)

    out["valor_fatura"] = _to_float(out["valor_fatura"], 0.0)

    if out["aliquota_icms"] is not None:
        try:
            out["aliquota_icms"] = _to_float(out["aliquota_icms"], 0.0)
        except Exception:
            out["aliquota_icms"] = None

    if not isinstance(out["valores_em_aberto"], list):
        out["valores_em_aberto"] = []

    for b in [
        "alta_tensao", "baixa_renda", "energia_ativa_injetada", "energia_reativa",
        "orgao_publico", "parcelamentos", "tarifa_branca", "ths_verde", "faturas_venc",
    ]:
        out[b] = bool(out[b])

    cleaned = []
    for item in out["valores_em_aberto"]:
        if not isinstance(item, dict):
            continue
        mes_ano = str(item.get("mes_ano", "")).strip()
        valor = _to_float(item.get("valor", 0.0), 0.0)
        cleaned.append({"mes_ano": mes_ano, "valor": valor})
    out["valores_em_aberto"] = cleaned

    # Valida consumo_lista
    if not isinstance(out.get("consumo_lista"), list):
        out["consumo_lista"] = []
    consumo_cleaned = []
    for item in out["consumo_lista"]:
        if not isinstance(item, dict):
            continue
        mes_ano = str(item.get("mes_ano", "")).strip()
        consumo = item.get("consumo")
        try:
            consumo_int = int(consumo) if consumo is not None else 0
        except (ValueError, TypeError):
            consumo_int = 0
        consumo_cleaned.append({"mes_ano": mes_ano, "consumo": consumo_int})
    out["consumo_lista"] = consumo_cleaned

    return out


def _read_customer_address_prompt(concessionaria: str = "", uf: str = "") -> str:
    """Carrega prompt específico para extração de nome do cliente e endereço"""
    # Carrega regras específicas da concessionária se disponível
    spec_prompt = ""
    try:
        mapper = _load_prompt_map()
        prompts = mapper.get("prompts", {}) if isinstance(mapper.get("prompts", {}), dict) else {}
        aliases = mapper.get("aliases", {}) if isinstance(mapper.get("aliases", {}), dict) else {}
        
        concessionaria_key = _key(concessionaria)
        aliased = aliases.get(concessionaria_key)
        if isinstance(aliased, str) and aliased.strip():
            concessionaria_key = _key(aliased)
        uf_key = _key(uf)
        
        spec_filename: str | None = None
        by_uf = prompts.get(concessionaria_key)
        if isinstance(by_uf, dict):
            v = by_uf.get(uf_key) or by_uf.get("*")
            if isinstance(v, str) and v.strip():
                spec_filename = v.strip()
        elif isinstance(by_uf, str) and by_uf.strip():
            spec_filename = by_uf.strip()
        
        if spec_filename:
            spec_path = PROMPTS_DIR / spec_filename
            if spec_path.exists():
                spec_content = spec_path.read_text(encoding="utf-8").strip()
                # Extrai apenas a seção de ENDEREÇO DO CLIENTE
                if "ENDEREÇO DO CLIENTE" in spec_content:
                    start_idx = spec_content.find("ENDEREÇO DO CLIENTE")
                    end_idx = spec_content.find("==========================", start_idx + 1)
                    if end_idx == -1:
                        end_idx = len(spec_content)
                    spec_prompt = spec_content[start_idx:end_idx].strip()
    except Exception:
        pass
    
    base_path = PROMPTS_DIR / "customer_address.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")
    
    base_prompt = base_path.read_text(encoding="utf-8").strip()
    
    if spec_prompt:
        return f"""{base_prompt}

REGRAS ESPECÍFICAS DA CONCESSIONÁRIA:
{spec_prompt}"""
    
    return base_prompt


def _read_consumption_prompt() -> str:
    """Carrega prompt específico para extração de consumo médio"""
    path = PROMPTS_DIR / "consumption.md"
    if not path.exists():
        raise RuntimeError(f"Arquivo {path.as_posix()} não encontrado.")
    return path.read_text(encoding="utf-8").strip()


async def _infer_one(img: Image.Image, prompt_text: str) -> str:
    if not (_HAS_MLX_VLM and MODEL is not None and PROCESSOR is not None and CONFIG is not None):
        raise RuntimeError("Dependência/Modelo MLX-VLM indisponível para inferência.")

    # Valida tamanho da imagem antes de processar
    w, h = img.size
    pixels = w * h
    if pixels > settings.max_pixels:
        raise ValueError(
            f"Imagem muito grande: {w}x{h} ({pixels:,} pixels). "
            f"Máximo permitido: {settings.max_pixels:,} pixels. "
            f"Redimensione a imagem antes de enviar."
        )
    
    # Validação de tamanho já feita acima (max_pixels)
    # Removida verificação de memória Metal (API mlx.metal deprecated)

    images = [img]
    
    log(f"[infer] processando imagem: {w}x{h} ({pixels:,} pixels)")

    formatted_prompt = apply_chat_template(
        PROCESSOR,
        CONFIG,
        prompt_text,
        num_images=len(images),
    )
    
    # Log do prompt formatado (primeiros 300 chars) para debug
    log(f"[infer] prompt formatado (primeiros 300 chars): {str(formatted_prompt)[:300]}")

    loop = asyncio.get_running_loop()

    def _run() -> str:
        # Lock entre processos para proteger operações Metal
        # Metal não suporta acesso concorrente mesmo de processos diferentes
        # Isso garante que apenas uma operação Metal ocorra por vez em todo o sistema
        with MetalLock():
            try:
                result = generate(
                    MODEL,
                    PROCESSOR,
                    formatted_prompt,
                    images,
                    verbose=True,  # Ativado para debug - mostra progresso da geração
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                )
                # MLX-VLM pode retornar GenerationResult ou string diretamente
                # Extrai o texto em ambos os casos
                if hasattr(result, 'text'):
                    return result.text
                elif hasattr(result, '__str__'):
                    return str(result)
                elif isinstance(result, str):
                    return result
                else:
                    # Tenta converter para string
                    return str(result)
            finally:
                # Limpa cache do Metal após inferência (CRÍTICO para evitar acúmulo)
                _clear_metal_cache()
                # Força garbage collection
                gc.collect()

    return await asyncio.wait_for(
        loop.run_in_executor(None, _run),
        timeout=settings.request_timeout_s,
    )


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model": settings.model_id,
        "max_concurrency": settings.max_concurrency,
        "mlx_vlm_available": _HAS_MLX_VLM,
    }


@app.post("/extract/energy")
async def extract_energy(
    concessionaria: str = Form(...),
    uf: str = Form(...),
    file: UploadFile = File(...),
):
    t_request_start = time.time()
    log(f"[req] requisição recebida: concessionaria={concessionaria}, uf={uf}")
    
    if not _HAS_MLX_VLM:
        raise HTTPException(
            status_code=503,
            detail=(
                "Dependência 'mlx-vlm' não instalada/ativa (import mlx_vlm falhou). "
                "Ative o venv do projeto ou rode via `uv run ...`."
            ),
        )

    if not concessionaria.strip():
        raise HTTPException(status_code=400, detail="concessionaria é obrigatório")
    if not uf.strip():
        raise HTTPException(status_code=400, detail="uf é obrigatório")

    if file.content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(status_code=400, detail=f"content-type não suportado: {file.content_type}")

    raw = await file.read()
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"imagem acima do limite de {settings.max_image_mb}MB")

    t_start = time.time()
    log(f"[timing] início processamento: {(t_start - t_request_start)*1000:.1f}ms após receber requisição")
    
    img = None
    img_temp_path = None
    customer_crop_img = None
    consumption_crop_img = None
    customer_crop_path = None
    consumption_crop_path = None
    
    try:
        t_load_start = time.time()
        img = _load_image(raw)
        # Libera os bytes da imagem imediatamente após carregar
        del raw
        gc.collect()
        t_load_end = time.time()
        log(f"[timing] carregamento imagem: {(t_load_end - t_load_start)*1000:.1f}ms")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"falha ao abrir imagem: {e}")

    # Salva imagem temporariamente para detecção YOLO
    if _HAS_OBJECT_DETECTION and OBJECT_DETECTOR is not None:
        try:
            t_crop_start = time.time()
            img_temp_path = _save_image_temp(img)
            log(f"[crop] imagem salva temporariamente: {img_temp_path}")
            
            # Faz recorte de dados do cliente
            try:
                t_customer_start = time.time()
                customer_crop_path = OBJECT_DETECTOR.detect_and_crop_customer_data(img_temp_path)
                t_customer_end = time.time()
                log(f"[timing] detecção cliente: {(t_customer_end - t_customer_start)*1000:.1f}ms")
                if customer_crop_path:
                    customer_crop_img = Image.open(customer_crop_path).convert("RGB")
                    log(f"[crop] recorte cliente/endereço criado: {customer_crop_path}")
            except Exception as e:
                log(f"[crop] erro ao recortar cliente/endereço: {e}")
            
            # Faz recorte de consumo
            try:
                t_consumption_start = time.time()
                consumption_crop_path = OBJECT_DETECTOR.detect_and_crop_consumption(img_temp_path)
                t_consumption_end = time.time()
                log(f"[timing] detecção consumo: {(t_consumption_end - t_consumption_start)*1000:.1f}ms")
                if consumption_crop_path:
                    consumption_crop_img = Image.open(consumption_crop_path).convert("RGB")
                    log(f"[crop] recorte consumo criado: {consumption_crop_path}")
            except Exception as e:
                log(f"[crop] erro ao recortar consumo: {e}")
            
            t_crop_end = time.time()
            log(f"[timing] total recortes: {(t_crop_end - t_crop_start)*1000:.1f}ms")
        except Exception as e:
            log(f"[crop] erro ao processar recortes: {e}")

    t0 = time.time()
    log(f"[timing] tempo até início inferências: {(t0 - t_start)*1000:.1f}ms")
    
    # Prompt para imagem completa (dados gerais)
    prompt_full = _read_prompt(concessionaria, uf)
    prompt_full = f"""{prompt_full}

Contexto da requisição: UF={uf}, Concessionária={concessionaria}

Agora analise a imagem e retorne o JSON com os dados extraídos:"""
    
    log(f"[prompt] tamanho do prompt completo: {len(prompt_full)} caracteres")

    # Resultados das 3 inferências
    result_full = None
    result_customer = None
    result_consumption = None
    
    try:
        t_gate_start = time.time()
        async with _GATE:
            t_gate_acquired = time.time()
            log(f"[timing] espera no semáforo: {(t_gate_acquired - t_gate_start)*1000:.1f}ms")
            
            # Inferência 1: Imagem completa (dados gerais)
            try:
                t_infer1_start = time.time()
                log("[infer] iniciando inferência imagem completa")
                result_full = await _infer_one(img, prompt_full)
                t_infer1_end = time.time()
                log(f"[timing] inferência completa: {(t_infer1_end - t_infer1_start)*1000:.1f}ms")
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="timeout na inferência do modelo (imagem completa)")
            except Exception as e:
                log(f"[infer] erro na inferência imagem completa: {e}")
                result_full = None
            
            # Inferência 2: Recorte cliente/endereço
            if customer_crop_img is not None:
                try:
                    t_infer2_start = time.time()
                    log("[infer] iniciando inferência recorte cliente/endereço")
                    prompt_customer = _read_customer_address_prompt(concessionaria, uf)
                    result_customer = await _infer_one(customer_crop_img, prompt_customer)
                    t_infer2_end = time.time()
                    log(f"[timing] inferência cliente: {(t_infer2_end - t_infer2_start)*1000:.1f}ms")
                except Exception as e:
                    log(f"[infer] erro na inferência cliente/endereço: {e}")
                    result_customer = None
            else:
                result_customer = None
            
            # Inferência 3: Recorte consumo
            if consumption_crop_img is not None:
                try:
                    t_infer3_start = time.time()
                    log("[infer] iniciando inferência recorte consumo")
                    prompt_consumption = _read_consumption_prompt()
                    result_consumption = await _infer_one(consumption_crop_img, prompt_consumption)
                    t_infer3_end = time.time()
                    log(f"[timing] inferência consumo: {(t_infer3_end - t_infer3_start)*1000:.1f}ms")
                except Exception as e:
                    log(f"[infer] erro na inferência consumo: {e}")
                    result_consumption = None
            else:
                result_consumption = None
    finally:
        # Limpa imagens da memória
        if img is not None:
            img.close()
            del img
        if customer_crop_img is not None:
            customer_crop_img.close()
            del customer_crop_img
        if consumption_crop_img is not None:
            consumption_crop_img.close()
            del consumption_crop_img
        
        # Remove arquivos temporários
        if img_temp_path and os.path.exists(img_temp_path):
            try:
                os.unlink(img_temp_path)
            except Exception:
                pass
        
        # Limpa arquivos temporários do ObjectDetection
        if _HAS_OBJECT_DETECTION and OBJECT_DETECTOR is not None:
            try:
                OBJECT_DETECTOR.cleanup_temp_files()
            except Exception:
                pass
        
        # Limpa cache do Metal e força garbage collection
        _clear_metal_cache()
        gc.collect()

    # Processa resultados e combina
    payload_full = {}
    payload_customer = {}
    payload_consumption = {}
    
    # Extrai JSON da inferência completa
    if result_full:
        try:
            payload_full = _extract_json(result_full)
            log(f"[infer] JSON imagem completa extraído: {json.dumps(payload_full, ensure_ascii=False)[:200]}")
        except Exception as e:
            log(f"[infer] ERRO ao extrair JSON imagem completa: {e}")
            log(f"[infer] resposta completa: {result_full[:500]}")
    
    # Extrai JSON do recorte cliente/endereço
    if result_customer:
        try:
            payload_customer = _extract_json(result_customer)
            log(f"[infer] JSON cliente/endereço extraído: {json.dumps(payload_customer, ensure_ascii=False)[:200]}")
        except Exception as e:
            log(f"[infer] ERRO ao extrair JSON cliente/endereço: {e}")
    
    # Extrai JSON do recorte consumo
    if result_consumption:
        try:
            payload_consumption = _extract_json(result_consumption)
            log(f"[infer] JSON consumo extraído: {json.dumps(payload_consumption, ensure_ascii=False)[:200]}")
        except Exception as e:
            log(f"[infer] ERRO ao extrair JSON consumo: {e}")
    
    # Combina resultados: dados gerais da imagem completa
    payload = payload_full.copy()
    
    # Sobrescreve com dados do endereço (sem nome_cliente) se disponível
    # O nome_cliente vem apenas da inferência principal, não do crop
    if payload_customer:
        for key in ["rua", "numero", "complemento", "bairro", "cidade", "estado", "cep"]:
            if key in payload_customer and payload_customer[key]:
                payload[key] = payload_customer[key]
    
    # Adiciona consumo_lista se disponível
    if payload_consumption and "consumo_lista" in payload_consumption:
        payload["consumo_lista"] = payload_consumption["consumo_lista"]
    
    payload = _ensure_contract(payload, concessionaria_input=concessionaria)

    ms = int((time.time() - t0) * 1000)
    log(f"[req] concessionaria={concessionaria.lower()} uf={uf.upper()} ms={ms}")
    _log_system_metrics("[req][mem]")

    return JSONResponse(content=payload)
