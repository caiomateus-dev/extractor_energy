"""Inference: model bootstrap, VLM generate."""

from inference.model import (
    CONFIG,
    GATE,
    MODEL,
    OBJECT_DETECTOR,
    PROCESSOR,
    clear_metal_cache,
    has_mlx_vlm,
    has_object_detection,
)
from inference.vlm import infer_one

__all__ = [
    "CONFIG",
    "GATE",
    "MODEL",
    "OBJECT_DETECTOR",
    "PROCESSOR",
    "clear_metal_cache",
    "has_mlx_vlm",
    "has_object_detection",
    "infer_one",
]
