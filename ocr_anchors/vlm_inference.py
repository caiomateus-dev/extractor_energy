"""VLM inference for small crops"""
from __future__ import annotations

import asyncio
import gc
import json
import os
import sys
import tempfile
import subprocess
import re
from typing import Dict, Any, Optional
from PIL import Image

from config import settings


def log(msg: str) -> None:
    """Log message"""
    print(msg, flush=True)


async def infer_field(img: Image.Image, prompt: str, field_name: str) -> Optional[Dict[str, Any]]:
    """Run VLM inference on a small crop with short prompt
    
    Args:
        img: Cropped image
        prompt: Short prompt for field extraction
        field_name: Name of field being extracted
        
    Returns:
        Extracted field value or None
    """
    if not hasattr(settings, 'model_id'):
        raise RuntimeError("Model not configured")
    
    # Save image temporarily
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    try:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(temp_img.name, format='JPEG', quality=95)
        temp_img_path = temp_img.name
    except Exception as e:
        log(f"[ocr_anchors] erro ao salvar imagem temporária: {e}")
        return None
    
    loop = asyncio.get_running_loop()
    
    def _run() -> Optional[str]:
        try:
            cmd = [
                sys.executable, "-m", "mlx_vlm.generate",
                "--model", settings.model_id,
                "--max-tokens", "200",  # Short prompts = less tokens
                "--temperature", str(settings.temperature),
                "--verbose",
                "--prompt", prompt,
                "--image", temp_img_path,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # Shorter timeout for small crops
            )
            
            if result.returncode != 0:
                log(f"[ocr_anchors] erro no subprocesso para {field_name}: {result.stderr[:200]}")
                return None
            
            output = result.stdout.strip()
            
            # Extract JSON from output
            # Try to find complete JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Fallback: try simpler pattern
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                try:
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            return None
        finally:
            try:
                if os.path.exists(temp_img_path):
                    os.unlink(temp_img_path)
            except Exception:
                pass
            gc.collect()
    
    try:
        result = await loop.run_in_executor(None, _run)
        return result
    except Exception as e:
        log(f"[ocr_anchors] erro na inferência de {field_name}: {e}")
        return None
