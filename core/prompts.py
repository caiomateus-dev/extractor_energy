"""Prompt loading: mapper, base + spec, customer_address, consumption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import settings

PROMPTS_DIR = Path(settings.prompts_dir).resolve()
ADAPTERS_DIR = Path(settings.adapters_dir).resolve()

_PROMPT_MAP_CACHE: dict[str, Any] | None = None
_PROMPT_MAP_MTIME_NS: int | None = None


def key_normalize(s: str) -> str:
    """Normaliza chaves (ex: CEMIG-D -> cemig-d). Mantém [a-z0-9], separadores em '-'."""
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


def load_prompt_map() -> dict[str, Any]:
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


def read_prompt(concessionaria: str, uf: str) -> str:
    base_path = PROMPTS_DIR / "base.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")
    base = base_path.read_text(encoding="utf-8").strip()
    mapper = load_prompt_map()
    prompts = mapper.get("prompts", {}) if isinstance(mapper.get("prompts", {}), dict) else {}
    aliases = mapper.get("aliases", {}) if isinstance(mapper.get("aliases", {}), dict) else {}
    concessionaria_key = key_normalize(concessionaria)
    aliased = aliases.get(concessionaria_key)
    if isinstance(aliased, str) and aliased.strip():
        concessionaria_key = key_normalize(aliased)
    uf_key = key_normalize(uf)
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


def read_customer_address_prompt(concessionaria: str = "", uf: str = "") -> str:
    base_path = PROMPTS_DIR / "customer_address.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")
    return base_path.read_text(encoding="utf-8").strip()


def read_consumption_prompt() -> str:
    path = PROMPTS_DIR / "consumption.md"
    if not path.exists():
        raise RuntimeError(f"Arquivo {path.as_posix()} não encontrado.")
    return path.read_text(encoding="utf-8").strip()


def read_retry_cep_prompt() -> str:
    path = PROMPTS_DIR / "retry_cep.md"
    if not path.exists():
        raise RuntimeError(f"Arquivo {path.as_posix()} não encontrado.")
    return path.read_text(encoding="utf-8").strip()
