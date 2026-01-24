"""VLM inference (in-process MLX-VLM generate)."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from PIL import Image

from config import settings
from core.logging_metrics import log

from inference.model import (
    CONFIG,
    GATE,
    MODEL,
    PROCESSOR,
    clear_metal_cache,
    has_mlx_vlm,
)

if has_mlx_vlm:
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template


async def infer_one(
    img: Image.Image,
    prompt_text: str,
    adapter_path: Path | None = None,
) -> str:
    """Inferência in-process. Modelo carregado no boot."""
    if not has_mlx_vlm:
        raise RuntimeError("mlx-vlm indisponível.")
    if MODEL is None or PROCESSOR is None or CONFIG is None:
        raise RuntimeError("Modelo não carregado.")
    w, h = img.size
    px = w * h
    if px > settings.max_pixels:
        raise ValueError(
            f"Imagem grande: {w}x{h} ({px:,} px). Máx: {settings.max_pixels:,}."
        )
    log(f"[infer] img {w}x{h} ({px:,} px)")
    if adapter_path and adapter_path.exists():
        log(f"[infer] adapter {adapter_path} ignorado (in-process usa base).")
    if img.mode != "RGB":
        img = img.convert("RGB")
    images = [img]

    def _run() -> str:
        try:
            fmt = apply_chat_template(
                PROCESSOR, CONFIG, prompt_text, num_images=len(images)
            )
            res = generate(
                MODEL,
                PROCESSOR,
                fmt,
                images,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                verbose=False,
                kv_bits=4,
                quantized_kv_start=0,
            )
            raw = getattr(res, "text", res)
            if not isinstance(raw, str):
                raw = str(raw)
            out = raw.strip()
            out = re.sub(r"(?<=\d),(?=\d)", ".", out)
            return out
        finally:
            clear_metal_cache()

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run)
