"""VLM inference: subprocess (mlx_vlm CLI) ou in-process."""

from __future__ import annotations

import asyncio
import gc
import json
import os
import re
import subprocess
import sys
import tempfile
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


def _find_balanced_json(text: str, start_char: str = "{") -> str | None:
    """Encontra JSON com chaves/colchetes balanceados. Tenta fechar se cortado."""
    if start_char == "{":
        end_char = "}"
        open_char, close_char = "{", "}"
    else:
        end_char = "]"
        open_char, close_char = "[", "]"
    start_pos = text.find(start_char)
    if start_pos == -1:
        return None
    depth = 0
    in_string = False
    escape_next = False
    last_valid_pos = start_pos
    for i in range(start_pos, len(text)):
        char = text[i]
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start_pos : i + 1]
            elif depth > 0:
                last_valid_pos = i
    if depth > 0:
        potential = text[start_pos : last_valid_pos + 1] + close_char * depth
        try:
            json.loads(potential)
            return potential
        except json.JSONDecodeError:
            return text[start_pos : last_valid_pos + 1] if last_valid_pos > start_pos else None
    return None


def _parse_subprocess_stdout(output: str) -> str:
    """Extrai JSON da saída do mlx_vlm.generate (stdout)."""
    lines = output.split("\n")
    filtered = []
    for line in lines:
        low = line.lower().strip()
        if any(x in low for x in ["deprecated", "calling", "python -m"]):
            continue
        filtered.append(line)
    cleaned = "\n".join(filtered).strip()
    marker = "<|im_start|>assistant"
    pos = cleaned.find(marker)
    if pos >= 0:
        section = cleaned[pos + len(marker) :].strip()
        section = re.sub(r"<\|[^|]+\|>", "", section).strip()
        section = re.sub(r"```json\s*", "", section)
        section = re.sub(r"\s*```", "", section).strip()
        js = section.find("{")
        if js != -1:
            balanced = _find_balanced_json(section[js:], "{")
            if balanced:
                try:
                    json.loads(balanced)
                    return re.sub(r"(?<=\d),(?=\d)", ".", balanced)
                except json.JSONDecodeError:
                    pass
        lst = section.find("[")
        if lst != -1:
            balanced = _find_balanced_json(section[lst:], "[")
            if balanced:
                try:
                    json.loads(balanced)
                    return re.sub(r"(?<=\d),(?=\d)", ".", balanced)
                except json.JSONDecodeError:
                    pass
        return re.sub(r"(?<=\d),(?=\d)", ".", section)
    cleaned = re.sub(r"```json\s*\n?", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"\n?\s*```\s*$", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = cleaned.strip()
    candidates = []
    idx = 0
    while True:
        idx = cleaned.find("{", idx)
        if idx == -1:
            break
        balanced = _find_balanced_json(cleaned[idx:], "{")
        if balanced:
            try:
                parsed = json.loads(balanced)
                candidates.append((idx, balanced, len(str(parsed))))
            except json.JSONDecodeError:
                pass
        idx += 1
    if candidates:
        for _, js, _ in candidates:
            try:
                p = json.loads(js)
                if isinstance(p, dict) and "consumo_lista" in p:
                    lst = p.get("consumo_lista", [])
                    if isinstance(lst, list) and len(lst) <= 13:
                        return re.sub(r"(?<=\d),(?=\d)", ".", js)
            except json.JSONDecodeError:
                continue
        _, out, _ = candidates[0]
        return re.sub(r"(?<=\d),(?=\d)", ".", out)
    return re.sub(r"(?<=\d),(?=\d)", ".", cleaned)


async def _infer_subprocess(
    img: Image.Image,
    prompt_text: str,
    adapter_path: Path | None = None,
    debug_label: str | None = None,
) -> str:
    """Inferência via subprocess (python -m mlx_vlm.generate)."""
    if not has_mlx_vlm:
        raise RuntimeError("mlx-vlm indisponível.")
    w, h = img.size
    px = w * h
    if px > settings.max_pixels:
        raise ValueError(
            f"Imagem grande: {w}x{h} ({px:,} px). Máx: {settings.max_pixels:,}."
        )
    log(f"[infer] img {w}x{h} ({px:,} px) [subprocess]")
    if img.mode != "RGB":
        img = img.convert("RGB")
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp_prompt_path: str | None = None
    try:
        img.save(tmp_img.name, format="JPEG", quality=95)
        path_img = tmp_img.name
        use_prompt_file = len(prompt_text) > 8000
        if use_prompt_file:
            f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8")
            f.write(prompt_text)
            f.close()
            tmp_prompt_path = f.name
        cmd = [
            sys.executable, "-m", "mlx_vlm", "generate",
            "--model", settings.model_id,
            "--max-tokens", str(settings.max_tokens),
            "--temperature", str(settings.temperature),
            "--verbose",
        ]
        if adapter_path and adapter_path.exists():
            cmd.extend(["--adapter-path", str(adapter_path)])
        if use_prompt_file and tmp_prompt_path:
            with open(tmp_prompt_path, "r", encoding="utf-8") as f:
                cmd.extend(["--prompt", f.read()])
        else:
            cmd.extend(["--prompt", prompt_text])
        cmd.extend(["--image", path_img])

        def _run() -> str:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.request_timeout_s,
            )
            if settings.debug:
                lbl = f" [{debug_label}]" if debug_label else ""
                log(f"[debug] SAÍDA BRUTA (subprocess){lbl} STDOUT:\n{r.stdout}")
                if r.stderr:
                    log(f"[debug] SAÍDA BRUTA (subprocess){lbl} STDERR:\n{r.stderr}")
            if r.returncode != 0:
                err = r.stderr or r.stdout or "Erro desconhecido"
                log(f"[infer] subprocess exit {r.returncode}: {err[:300]}")
                raise RuntimeError(f"Subprocess falhou: {err[:200]}")
            return _parse_subprocess_stdout(r.stdout.strip())

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)
    finally:
        try:
            if os.path.exists(tmp_img.name):
                os.unlink(tmp_img.name)
        except Exception:
            pass
        if tmp_prompt_path and os.path.exists(tmp_prompt_path):
            try:
                os.unlink(tmp_prompt_path)
            except Exception:
                pass


async def _infer_in_process(
    img: Image.Image,
    prompt_text: str,
    adapter_path: Path | None = None,
    debug_label: str | None = None,
) -> str:
    """Inferência in-process (MLX-VLM generate)."""
    if not has_mlx_vlm or MODEL is None or PROCESSOR is None or CONFIG is None:
        raise RuntimeError("Modelo não carregado ou mlx-vlm indisponível.")
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
            )
            raw = getattr(res, "text", res)
            if not isinstance(raw, str):
                raw = str(raw)
            if settings.debug:
                lbl = f" [{debug_label}]" if debug_label else ""
                log(f"[debug] SAÍDA BRUTA (in-process){lbl}:\n{raw}")
            out = raw.strip()
            out = re.sub(r"(?<=\d),(?=\d)", ".", out)
            return out
        finally:
            clear_metal_cache()
            gc.collect()

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run)


async def infer_one(
    img: Image.Image,
    prompt_text: str,
    adapter_path: Path | None = None,
    debug_label: str | None = None,
) -> str:
    """Inferência: subprocess ou in-process conforme config."""
    if settings.use_subprocess:
        return await _infer_subprocess(img, prompt_text, adapter_path, debug_label)
    return await _infer_in_process(img, prompt_text, adapter_path, debug_label)
