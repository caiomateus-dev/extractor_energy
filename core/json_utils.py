"""Extract JSON from model output (markdown, deprecation lines, etc.)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def extract_json(text: str) -> Dict[str, Any] | list:
    """Extrai JSON do texto. Retorna dict ou list."""
    text = text.strip()
    text = re.sub(r"```json\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?\s*```\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*```\s*\n?", "", text, flags=re.MULTILINE | re.IGNORECASE)
    lines = text.split("\n")
    filtered = []
    skip = False
    for line in lines:
        low = line.lower().strip()
        if any(x in low for x in ["deprecated", "calling", "python -m", "==========", "files:", "prompt:"]):
            skip = True
            continue
        if "{" in line or "[" in line:
            skip = False
        if not skip:
            filtered.append(line)
    text = "\n".join(filtered).strip()

    if text.startswith("[") and text.endswith("]"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    m = re.search(r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    if start != -1:
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if not in_str:
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        s = re.sub(r",\s*]", "]", m.group(0))
        s = re.sub(r",\s*}", "}", s)
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        s = m.group(0)
        s = re.sub(r",\s*}", "}", s)
        s = re.sub(r",\s*]", "]", s)
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            raise ValueError(f"Nenhum JSON válido. {e}. Texto: {text[:500]}")
    raise ValueError(f"Nenhum JSON encontrado. Texto: {text[:500]}")
