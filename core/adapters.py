"""LoRA adapter resolution by concessionária/UF."""

from __future__ import annotations

from pathlib import Path

from config import settings
from .prompts import ADAPTERS_DIR, key_normalize


def find_adapter_path(concessionaria: str, uf: str) -> Path | None:
    """Retorna adapters/{concessionaria}_{uf}/ se existir e tiver adapter, senão None."""
    if not settings.use_lora_adapters:
        return None
    c = key_normalize(concessionaria)
    u = key_normalize(uf)
    adapter_name = f"{c}_{u}"
    path = ADAPTERS_DIR / adapter_name
    if not path.exists() or not path.is_dir():
        return None
    files = (
        list(path.glob("adapter*.safetensors"))
        + list(path.glob("adapter*.bin"))
        + list(path.glob("adapter_config.json"))
    )
    return path if files else None
