from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    model_id: str = "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"

    # Valores conservadores para evitar alocações gigantes no Metal (limite de buffer).
    max_tokens: int = 900
    temperature: float = 0.0

    max_image_mb: int = 12
    # Reduzido drasticamente para evitar alocações excessivas no Metal
    # 10M pixels pode resultar em tensores de ~80GB+ durante processamento
    # 1.5M pixels é suficiente para OCR de documentos e reduz alocação para ~12GB
    max_pixels: int = 1_500_000
    max_concurrency: int = 2
    request_timeout_s: int = 45

    prompts_dir: str = "prompts"


settings = Settings()
