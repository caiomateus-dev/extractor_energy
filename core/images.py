"""Image loading, temp save, enhancement."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance

from config import settings
from .logging_metrics import log


def save_image_temp(img: Image.Image) -> str:
    """Salva imagem PIL em arquivo temporário para uso com YOLO."""
    f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    path = f.name
    f.close()
    img.save(path, format="PNG")
    return path


def load_image(raw: bytes) -> Image.Image:
    """Carrega imagem, redimensiona se passar de max_pixels."""
    bio = io.BytesIO(raw)
    try:
        img = Image.open(bio).convert("RGB")
        w, h = img.size
        pixels = w * h
        if pixels > settings.max_pixels:
            log(f"[img] imagem grande: {w}x{h} ({pixels:,} px) - redimensionando")
        if pixels > settings.max_pixels:
            scale = (settings.max_pixels / float(pixels)) ** 0.5
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            log(f"[img] redimensionada: {nw}x{nh} ({nw * nh:,} px)")
        out = img.copy()
        img.close()
    finally:
        bio.close()
    return out


def enhance_address_image(img: Image.Image) -> Image.Image:
    """Aplica contraste na imagem de endereço."""
    try:
        enhancer = ImageEnhance.Contrast(img)
        out = enhancer.enhance(1.3)
        log("[img] contraste aplicado (endereço)")
        return out
    except Exception as e:
        log(f"[img] erro contraste: {e}, usando original")
        return img
