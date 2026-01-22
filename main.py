from __future__ import annotations

import asyncio
import gc
import io
import json
import os
import sys
import time
from pathlib import Path
from importlib.util import find_spec
from typing import Any, Dict
import re

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from config import settings

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
    out: Dict[str, int] = {}
    try:
        import mlx.core as mx  # type: ignore

        metal = getattr(mx, "metal", None)
        if metal is None:
            return out

        for k, fn in [
            ("active", "get_active_memory"),
            ("peak", "get_peak_memory"),
            ("cache", "get_cache_memory"),
        ]:
            if hasattr(metal, fn):
                try:
                    v = getattr(metal, fn)()
                    if isinstance(v, int):
                        out[k] = v
                except Exception:
                    pass

        if hasattr(metal, "device_info"):
            try:
                info = metal.device_info()
                if isinstance(info, dict):
                    for key in ["memory_size", "recommended_max_working_set_size", "max_buffer_size"]:
                        v = info.get(key)
                        if isinstance(v, int):
                            out[key] = v
            except Exception:
                pass
    except Exception:
        pass
    return out


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
    metal = _metal_memory_bytes()
    metal_total = metal.get("memory_size")
    metal_active = metal.get("active")
    metal_wset = metal.get("recommended_max_working_set_size")
    metal_max_buffer = metal.get("max_buffer_size")
    metal_avail = None
    if isinstance(metal_total, int) and isinstance(metal_active, int):
        metal_avail = max(0, metal_total - metal_active)
    log(
        f"{tag} rss={_format_bytes(rss)} "
        f"ram_total={_format_bytes(total)} ram_avail={_format_bytes(avail)} "
        f"metal_active={_format_bytes(metal_active)} metal_peak={_format_bytes(metal.get('peak'))} "
        f"metal_cache={_format_bytes(metal.get('cache'))} metal_total={_format_bytes(metal_total)} "
        f"metal_max_buffer={_format_bytes(metal_max_buffer)} "
        f"metal_avail~={_format_bytes(metal_avail)} metal_wset={_format_bytes(metal_wset)}"
    )


MODEL = PROCESSOR = CONFIG = None
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


_GATE = asyncio.Semaphore(settings.max_concurrency)


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
    }

    out = dict(template)
    for k in template.keys():
        if k in payload:
            out[k] = payload[k]

    if not str(out.get("distribuidora", "")).strip():
        out["distribuidora"] = concessionaria_input

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

    return out


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
    
    # Verifica memória disponível do Metal antes de processar
    try:
        import mlx.core as mx  # type: ignore
        metal = getattr(mx, "metal", None)
        if metal is not None:
            device_info = metal.device_info()
            if isinstance(device_info, dict):
                max_buffer = device_info.get("max_buffer_size", 0)
                if isinstance(max_buffer, int) and max_buffer > 0:
                    # Estima memória necessária (conservador: ~50 bytes por pixel)
                    estimated_memory = pixels * 50
                    if estimated_memory > max_buffer * 0.8:  # Usa 80% do máximo como segurança
                        raise ValueError(
                            f"Imagem requer ~{estimated_memory / 1e9:.1f}GB, "
                            f"mas Metal permite apenas ~{max_buffer / 1e9:.1f}GB. "
                            f"Redimensione a imagem."
                        )
    except Exception:
        pass  # Se não conseguir verificar, continua (pode funcionar)

    images = [img]
    
    log(f"[infer] processando imagem: {w}x{h} ({pixels:,} pixels)")

    formatted_prompt = apply_chat_template(
        PROCESSOR,
        CONFIG,
        prompt_text,
        num_images=len(images),
    )

    loop = asyncio.get_running_loop()

    def _run() -> str:
        try:
            result = generate(
                MODEL,
                PROCESSOR,
                formatted_prompt,
                images,
                verbose=False,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
            )
            return result
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

    img = None
    try:
        img = _load_image(raw)
        # Libera os bytes da imagem imediatamente após carregar
        del raw
        gc.collect()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"falha ao abrir imagem: {e}")

    prompt = _read_prompt(concessionaria, uf)
    prompt = f"{prompt}\n\nContexto:\n- UF: {uf}\n- Concessionária: {concessionaria}\n"

    t0 = time.time()

    result_text = None
    try:
        async with _GATE:
            try:
                result_text = await _infer_one(img, prompt)
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="timeout na inferência do modelo")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"erro na inferência: {e}")
    finally:
        # Limpa a imagem da memória imediatamente após inferência
        if img is not None:
            img.close()
            del img
        # Limpa cache do Metal e força garbage collection
        _clear_metal_cache()
        gc.collect()

    try:
        payload = _extract_json(result_text)
    except Exception:
        payload = {}

    payload = _ensure_contract(payload, concessionaria_input=concessionaria)

    ms = int((time.time() - t0) * 1000)
    log(f"[req] concessionaria={concessionaria.lower()} uf={uf.upper()} ms={ms}")
    _log_system_metrics("[req][mem]")

    return JSONResponse(content=payload)
