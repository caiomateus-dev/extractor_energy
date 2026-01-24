from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    model_id: str = "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"

    # Inferência mais rápida: menos pixels = menos tokens visuais; max_tokens cobre JSON (~300–800).
    max_tokens: int = 1024
    temperature: float = 0.0

    max_image_mb: int = 12
    # ~1M px reduz encode vs 1.5M; ajuste se OCR piorar.
    max_pixels: int = 1_000_000
    # In-process: Metal NÃO é thread-safe. Só 1 inferência por worker (sempre 1).
    # Para 2+ req em paralelo: uvicorn main:app --workers 2
    max_concurrency: int = 1
    request_timeout_s: int = 45

    prompts_dir: str = "prompts"
    adapters_dir: str = "adapters"  # Diretório onde os adapters LoRA são armazenados
    use_lora_adapters: bool = True  # Se True, tenta carregar adapters LoRA quando disponíveis


settings = Settings()
