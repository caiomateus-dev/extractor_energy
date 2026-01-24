"""FastAPI routes: health, extract/energy."""

from __future__ import annotations

import asyncio
import gc
import time
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from config import settings
from core import (
    ensure_contract,
    extract_json,
    find_adapter_path,
    load_image,
    log,
    log_system_metrics,
    read_consumption_prompt,
    read_customer_address_prompt,
    read_prompt,
    save_image_temp,
)
from inference import (
    GATE,
    clear_metal_cache,
    has_mlx_vlm,
    has_object_detection,
    infer_one,
)
from inference.model import OBJECT_DETECTOR

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": settings.model_id,
        "max_concurrency": settings.max_concurrency,
        "mlx_vlm_available": has_mlx_vlm,
    }


@router.post("/extract/energy")
async def extract_energy(
    concessionaria: str = Form(...),
    uf: str = Form(...),
    file: UploadFile = File(...),
):
    t0 = time.time()
    log(f"[req] concessionaria={concessionaria} uf={uf}")

    adapter_path = find_adapter_path(concessionaria, uf)
    if adapter_path:
        log(f"[adapter] LoRA: {adapter_path}")
    else:
        log(f"[adapter] nenhum adapter para {concessionaria}/{uf}")

    if not has_mlx_vlm:
        raise HTTPException(
            status_code=503,
            detail="mlx-vlm não instalado. Use venv e `uv run ...`.",
        )
    if not concessionaria.strip():
        raise HTTPException(400, "concessionaria obrigatório")
    if not uf.strip():
        raise HTTPException(400, "uf obrigatório")
    if file.content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(400, f"content-type não suportado: {file.content_type}")

    raw = await file.read()
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(413, f"imagem > {settings.max_image_mb}MB")

    t_start = time.time()
    try:
        img = load_image(raw)
    except Exception as e:
        raise HTTPException(400, f"falha ao abrir imagem: {e}")
    del raw
    gc.collect()
    log(f"[timing] load {(time.time() - t_start) * 1000:.1f}ms")

    img_temp_path = None
    customer_crop_img = None
    consumption_crop_img = None

    if has_object_detection and OBJECT_DETECTOR is not None:
        try:
            img_temp_path = save_image_temp(img)
            try:
                p = OBJECT_DETECTOR.detect_and_crop_customer_data(img_temp_path)
                if p:
                    customer_crop_img = Image.open(p).convert("RGB")
                    log("[crop] cliente ok")
            except Exception as e:
                log(f"[crop] cliente: {e}")
            try:
                p = OBJECT_DETECTOR.detect_and_crop_consumption(img_temp_path)
                if p:
                    consumption_crop_img = Image.open(p).convert("RGB")
                    log("[crop] consumo ok")
            except Exception as e:
                log(f"[crop] consumo: {e}")
        except Exception as e:
            log(f"[crop] {e}")

    if settings.debug and (customer_crop_img is not None or consumption_crop_img is not None):
        _ts = int(time.time() * 1000)
        _c = "".join(c if c.isalnum() or c in "-_" else "_" for c in concessionaria.strip() or "x")[:60]
        _u = "".join(c if c.isalnum() or c in "-_" else "_" for c in uf.strip() or "x")[:10]
        _root = Path(__file__).resolve().parents[1]
        _dir = _root / "debug_crops"
        _dir.mkdir(parents=True, exist_ok=True)
        if customer_crop_img is not None:
            _p = _dir / f"customer_{_c}_{_u}_{_ts}.png"
            customer_crop_img.save(_p)
            log(f"[debug] crop salvo: {_p}")
        if consumption_crop_img is not None:
            _p = _dir / f"consumption_{_c}_{_u}_{_ts}.png"
            consumption_crop_img.save(_p)
            log(f"[debug] crop salvo: {_p}")

    t_infer = time.time()
    result_customer = None
    result_consumption = None
    result_full = None
    payload_customer = {}
    payload_consumption = {}

    async def _do_customer() -> None:
        nonlocal result_customer, payload_customer
        if customer_crop_img is None:
            return
        try:
            prompt_c = read_customer_address_prompt(concessionaria, uf)
            _label = "customer" if settings.debug else None
            result_customer = await infer_one(customer_crop_img, prompt_c, adapter_path, debug_label=_label)
            if result_customer:
                try:
                    payload_customer = extract_json(result_customer)
                except Exception as e:
                    log(f"[infer] JSON cliente: {e}")
        except Exception as e:
            log(f"[infer] cliente: {e}")

    async def _do_consumption() -> None:
        nonlocal result_consumption, payload_consumption
        if consumption_crop_img is None:
            return
        try:
            prompt_cons = read_consumption_prompt()
            _label = "consumption" if settings.debug else None
            result_consumption = await infer_one(
                consumption_crop_img, prompt_cons, adapter_path, debug_label=_label
            )
            if result_consumption:
                try:
                    payload_consumption = extract_json(result_consumption)
                except Exception as e:
                    log(f"[infer] JSON consumo: {e}")
                    payload_consumption = {"consumo_lista": []}
                else:
                    if not isinstance(payload_consumption, dict) or "consumo_lista" not in payload_consumption:
                        payload_consumption = {"consumo_lista": []}
                    else:
                        lst = payload_consumption["consumo_lista"]
                        if isinstance(lst, list) and len(lst) > 13:
                            payload_consumption["consumo_lista"] = lst[:13]
        except Exception as e:
            log(f"[infer] consumo: {e}")

    def _build_prompt_full() -> str:
        endereco_ctx = ""
        if payload_customer:
            c = payload_customer.get("cidade", "").strip()
            e = payload_customer.get("estado", "").strip()
            b = payload_customer.get("bairro", "").strip()
            r = payload_customer.get("rua", "").strip()
            if c or e or b or r:
                endereco_ctx = "\n\nIMPORTANTE - ENDEREÇO JÁ EXTRAÍDO:\n"
                endereco_ctx += "O endereço do cliente já foi extraído.\n"
                if r:
                    endereco_ctx += f"- Rua: {r}\n"
                if b:
                    endereco_ctx += f"- Bairro: {b}\n"
                if c:
                    endereco_ctx += f"- Cidade: {c}\n"
                if e:
                    endereco_ctx += f"- Estado: {e}\n"
                endereco_ctx += "\nCRÍTICO: nome_cliente NÃO deve conter endereço. Apenas nome da pessoa/empresa.\n"
        base = read_prompt(concessionaria, uf)
        return f"""{base}{endereco_ctx}

Contexto: UF={uf}, Concessionária={concessionaria}

Analise a imagem e retorne o JSON:"""

    _label_full = "full" if settings.debug else None
    if settings.use_subprocess:
        await asyncio.gather(_do_customer(), _do_consumption())
        prompt_full = _build_prompt_full()
        try:
            result_full = await infer_one(img, prompt_full, adapter_path, debug_label=_label_full)
        except Exception as e:
            log(f"[infer] full: {e}")
            result_full = None
    else:
        async with GATE:
            await _do_customer()
            await _do_consumption()
            prompt_full = _build_prompt_full()
            try:
                result_full = await infer_one(img, prompt_full, adapter_path, debug_label=_label_full)
            except Exception as e:
                log(f"[infer] full: {e}")
                result_full = None

    if img:
        img.close()
        del img
    if customer_crop_img:
        customer_crop_img.close()
        del customer_crop_img
    if consumption_crop_img:
        consumption_crop_img.close()
        del consumption_crop_img
    if img_temp_path and Path(img_temp_path).exists():
        try:
            Path(img_temp_path).unlink()
        except Exception:
            pass
    if has_object_detection and OBJECT_DETECTOR is not None:
        try:
            OBJECT_DETECTOR.cleanup_temp_files()
        except Exception:
            pass
    clear_metal_cache()
    gc.collect()

    payload_full = {}
    if result_full:
        try:
            payload_full = extract_json(result_full)
        except Exception as e:
            log(f"[infer] JSON full: {e}")

    payload = dict(payload_full)
    if payload_customer:
        for k in ["rua", "numero", "complemento", "bairro", "cidade", "estado", "cep"]:
            v = payload_customer.get(k)
            if not v or not str(v).strip():
                continue
            s = str(v).strip()
            if k == "cep":
                digits = "".join(c for c in s if c.isdigit())
                if len(digits) != 8:
                    continue
            if k == "estado":
                if len(s) != 2 or not s.isalpha():
                    continue
            payload[k] = v
    if payload_consumption and "consumo_lista" in payload_consumption:
        payload["consumo_lista"] = payload_consumption["consumo_lista"]

    payload = ensure_contract(payload, concessionaria, uf)
    ms = int((time.time() - t_infer) * 1000)
    log(f"[req] {concessionaria} {uf} {ms}ms")
    log_system_metrics("[req][mem]")
    return JSONResponse(content=payload)
