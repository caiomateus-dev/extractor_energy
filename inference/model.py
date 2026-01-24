"""Model bootstrap: MLX-VLM, object detector, concurrency gate."""

from __future__ import annotations

import asyncio
import sys
import time
from importlib.util import find_spec
from pathlib import Path

from config import settings

from core.logging_metrics import log, log_system_metrics

# Optional MLX-VLM
has_mlx_vlm = find_spec("mlx_vlm") is not None
if has_mlx_vlm:
    from mlx_vlm import load
    from mlx_vlm.utils import load_config
else:
    load = load_config = None

# Optional object detection (YOLO)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from detectors.object_detection import ObjectDetection
    has_object_detection = True
except ImportError as e:
    has_object_detection = False
    ObjectDetection = None
    log(f"[boot] object_detection não disponível: {e}")

MODEL = None
PROCESSOR = None
CONFIG = None
OBJECT_DETECTOR = None
GATE: asyncio.Semaphore | None = None


def clear_metal_cache() -> None:
    """Libera cache Metal/MLX após inferência."""
    try:
        import mlx.core as mx  # type: ignore
        if hasattr(mx, "clear_cache"):
            try:
                mx.clear_cache()
            except Exception:
                pass
        global MODEL
        if MODEL is not None and hasattr(MODEL, "parameters"):
            try:
                params = MODEL.parameters()
                if isinstance(params, dict):
                    mx.eval(list(params.values()))
            except Exception:
                pass
    except Exception:
        pass


def _boot_model() -> None:
    global MODEL, PROCESSOR, CONFIG, GATE
    # Metal não suporta 2+ inferências em paralelo no mesmo processo.
    # GATE=1 serializa. Paralelismo real: uvicorn --workers N.
    GATE = asyncio.Semaphore(1)
    if not has_mlx_vlm:
        log("[boot] mlx-vlm ausente. Use venv e `uv run uvicorn main:app --reload`.")
        return
    log(f"[boot] loading model: {settings.model_id}")
    MODEL, PROCESSOR = load(settings.model_id)
    CONFIG = load_config(settings.model_id)
    log("[boot] model loaded")
    log("[boot] Metal serializado (1 inferência/worker). Paralelo: uvicorn main:app --workers N")
    log_system_metrics("[boot][mem]")


def _boot_detector() -> None:
    global OBJECT_DETECTOR
    if not has_object_detection or ObjectDetection is None:
        return
    try:
        t0 = time.time()
        OBJECT_DETECTOR = ObjectDetection()
        log(f"[boot] object detector ok em {(time.time() - t0) * 1000:.1f}ms")
    except Exception as e:
        log(f"[boot] detector error: {e}")
        OBJECT_DETECTOR = None


_boot_model()
_boot_detector()
