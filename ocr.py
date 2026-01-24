"""Serviço interno de OCR (PaddleOCR). Sem API; uso via run_ocr + find_cep_in_ocr_items."""

from __future__ import annotations

import io
import logging
import os
import re
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel

# Evitar checagem de model hosters no import.
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

logger = logging.getLogger("ocr")

# CEPs inválidos (placeholders, genéricos).
_CEP_BLACKLIST = frozenset(
    {"00000000", "11111111", "22222222", "99999999", "12345678", "99999000"}
)


class OcrItem(BaseModel):
    text: str
    bbox: list[list[int]]


def _load_ocr_config() -> dict[str, Any]:
    pyproject_path = Path(__file__).resolve().with_name("pyproject.toml")
    if not pyproject_path.exists():
        return {}

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    tool_cfg = data.get("tool", {}) or {}
    for key in ("extractor_energy", "extractor-energy", "teste_validator"):
        app_cfg = tool_cfg.get(key, {}) or {}
        ocr_cfg = app_cfg.get("ocr", {}) or {}
        if ocr_cfg:
            return dict(ocr_cfg)
    return {}


@lru_cache(maxsize=1)
def _get_ocr():
    import inspect

    from paddleocr import PaddleOCR

    cfg = _load_ocr_config().copy()

    if cfg.get("disable_model_source_check", False):
        os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

    cfg["use_doc_unwarping"] = False
    cfg["use_doc_orientation_classify"] = False
    cfg["use_textline_orientation"] = True

    if "rec_image_shape" in cfg and "text_rec_input_shape" not in cfg:
        cfg["text_rec_input_shape"] = cfg["rec_image_shape"]

    def _parse_shape(v: Any) -> Any:
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            if parts and all(p.lstrip("-").isdigit() for p in parts):
                return [int(p) for p in parts]
        return v

    if "text_rec_input_shape" in cfg:
        cfg["text_rec_input_shape"] = _parse_shape(cfg["text_rec_input_shape"])
    if "text_det_input_shape" in cfg:
        cfg["text_det_input_shape"] = _parse_shape(cfg["text_det_input_shape"])

    cfg.setdefault("ocr_version", "PP-OCRv5")
    cfg.setdefault("lang", "pt")
    cfg.setdefault("text_det_limit_type", "max")
    cfg.setdefault("text_det_limit_side_len", 1536)
    cfg.setdefault("text_det_thresh", 0.3)
    cfg.setdefault("text_det_box_thresh", 0.6)
    cfg.setdefault("text_det_unclip_ratio", 2.0)
    cfg.setdefault("text_rec_score_thresh", 0.0)
    cfg.setdefault("textline_orientation_batch_size", 8)
    cfg.setdefault("text_recognition_batch_size", 8)

    sig = inspect.signature(PaddleOCR.__init__)
    allowed_keys = {k for k in sig.parameters.keys() if k not in {"self", "kwargs"}}
    init_kwargs = {k: v for k, v in cfg.items() if k in allowed_keys}

    return PaddleOCR(**init_kwargs)


def _to_bgr(image: bytes | Path | Any) -> np.ndarray:
    from PIL import Image

    if isinstance(image, Path):
        image = image.read_bytes()
    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image)).convert("RGB")
    else:
        # PIL Image
        img = image.convert("RGB") if hasattr(image, "convert") else Image.open(image).convert("RGB")
    rgb = np.asarray(img)
    return rgb[:, :, ::-1].copy()


def _poly_to_bbox(poly: Any) -> list[list[int]]:
    arr = np.asarray(poly)
    if arr.shape != (4, 2):
        arr = arr.reshape(4, 2)
    return [[int(x), int(y)] for x, y in arr.tolist()]


def _extract_items(pred: Any) -> list[OcrItem]:
    items: list[OcrItem] = []

    if isinstance(pred, list) and pred and isinstance(pred[0], dict):
        for page in pred:
            texts = page.get("rec_texts") or []
            polys = page.get("rec_polys") or []
            for text, poly in zip(texts, polys):
                if not text:
                    continue
                items.append(OcrItem(text=str(text), bbox=_poly_to_bbox(poly)))
        return items

    if isinstance(pred, list):
        for line in pred:
            if not isinstance(line, (list, tuple)) or len(line) < 2:
                continue
            poly, rec = line[0], line[1]
            text = rec[0] if isinstance(rec, (list, tuple)) and rec else ""
            if not text:
                continue
            items.append(OcrItem(text=str(text), bbox=_poly_to_bbox(poly)))

    return items


def run_ocr(image: bytes | Path | Any) -> list[OcrItem]:
    """
    Executa OCR na imagem. Aceita bytes, Path ou PIL Image.
    Retorna lista de OcrItem (texto + bbox). Síncrono; use asyncio.to_thread em contextos async.
    """
    bgr = _to_bgr(image)
    ocr = _get_ocr()
    pred_kwargs: dict[str, Any] = {
        "use_doc_unwarping": False,
        "use_doc_orientation_classify": False,
        "use_textline_orientation": True,
    }
    pred = ocr.predict(bgr, **pred_kwargs)
    return _extract_items(pred)


# Padrão CEP: NNNNN-NNN ou NNNNNNNN (8 dígitos). Ponto como separador: N.NNNN-NNN.
_CEP_RE = re.compile(
    r"(?:^|\D)(\d{5})[-.]?(\d{3})(?:\D|$)|(?:^|\D)(\d{8})(?:\D|$)"
)


def find_cep_in_ocr_items(items: list[OcrItem]) -> str | None:
    """
    Percorre os textos do OCR e retorna o primeiro CEP válido (8 dígitos).
    Ignora placeholders (00000000, 99999999, etc.) e números de 5 dígitos sem hífen.
    """
    for item in items:
        text = (item.text or "").strip()
        if not text:
            continue
        for m in _CEP_RE.finditer(text):
            if m.group(3):
                digits = m.group(3)
            else:
                digits = (m.group(1) or "") + (m.group(2) or "")
            if len(digits) != 8 or digits in _CEP_BLACKLIST:
                continue
            return digits
    return None


def has_ocr() -> bool:
    """Indica se PaddleOCR está disponível e o serviço pode ser usado."""
    try:
        import paddleocr  # noqa: F401
        return True
    except Exception:
        return False
