from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    model_id: str = "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"

    # Valores conservadores para evitar alocações gigantes no Metal (limite de buffer).
    # Aumentado para garantir que o JSON completo seja gerado (13 meses = ~600 tokens mínimo)
    max_tokens: int = 2000
    temperature: float = 0.0

    max_image_mb: int = 12
    # Reduzido drasticamente para evitar alocações excessivas no Metal
    # 10M pixels pode resultar em tensores de ~80GB+ durante processamento
    # 1.5M pixels é suficiente para OCR de documentos e reduz alocação para ~12GB
    max_pixels: int = 1_500_000
    # In-process: Metal NÃO é thread-safe. Só 1 inferência por worker (sempre 1).
    # Para 2+ req em paralelo: uvicorn main:app --workers 2
    max_concurrency: int = 1
    request_timeout_s: int = 45

    prompts_dir: str = "prompts"
    adapters_dir: str = "adapters"  # Diretório onde os adapters LoRA são armazenados
    use_lora_adapters: bool = True  # Se True, tenta carregar adapters LoRA quando disponíveis

    # Inferência via subprocess (python -m mlx_vlm.generate). Permite 3 inferências em paralelo
    # (customer || consumption, depois full). Sem subprocess: in-process + GATE (1 por worker).
    use_subprocess: bool = True


settings = Settings()
