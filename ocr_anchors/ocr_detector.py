"""OCR detector using PaddleOCR for text detection and bounding boxes"""
from __future__ import annotations

import re
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image
import numpy as np

try:
    from paddleocr import PaddleOCR
    _HAS_PADDLEOCR = True
except (ImportError, OSError, Exception) as e:
    _HAS_PADDLEOCR = False
    _PADDLEOCR_ERROR = str(e)


class OCRDetector:
    """Detects text and bounding boxes using PaddleOCR"""
    
    def __init__(self, lang: str = "pt"):
        """Initialize PaddleOCR detector
        
        Args:
            lang: Language code ('pt' for Portuguese, 'en' for English)
        """
        if not _HAS_PADDLEOCR:
            error_msg = _PADDLEOCR_ERROR if '_PADDLEOCR_ERROR' in globals() else "Unknown error"
            raise RuntimeError(
                f"PaddleOCR não está disponível. "
                f"Erro: {error_msg}\n"
                f"Verifique se PaddleOCR e PaddlePaddle estão instalados corretamente.\n"
                f"No macOS, pode ser necessário instalar dependências do sistema ou usar Docker."
            )
        
        try:
            # Initialize OCR with detection and recognition
            # use_angle_cls=False for faster processing (we assume upright text)
            self.ocr = PaddleOCR(
                use_angle_cls=False,
                lang=lang
            )
        except (ImportError, OSError, Exception) as e:
            error_detail = str(e)
            # Check if it's a library loading error
            if "Library not loaded" in error_detail or "dlopen" in error_detail:
                missing_lib = "biblioteca nativa"
                if "netcdf" in error_detail.lower():
                    missing_lib = "netcdf"
                raise RuntimeError(
                    f"Falha ao inicializar PaddleOCR: {error_detail}\n"
                    f"Pode ser necessário instalar dependências do sistema.\n"
                    f"Se o erro mencionar uma biblioteca específica, instale-a via Homebrew."
                ) from e
            raise RuntimeError(
                f"Falha ao inicializar PaddleOCR: {error_detail}"
            ) from e
    
    def detect_text_boxes(self, img: Image.Image) -> List[Dict[str, Any]]:
        """Detect text bounding boxes and extract text from image
        
        Args:
            img: PIL Image
            
        Returns:
            List of dicts with keys: 'bbox', 'text', 'score'
            bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        import tempfile
        import os
        
        # Ensure RGB format
        img_rgb = img.convert('RGB')
        
        # Save to temporary file - PaddleOCR works best with file paths
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        try:
            img_rgb.save(temp_img.name, format='JPEG', quality=95)
            temp_img_path = temp_img.name
        except Exception as e:
            temp_img.close()
            raise RuntimeError(f"Falha ao salvar imagem temporária: {e}") from e
        
        try:
            # Use file path - most reliable method according to docs
            result = self.ocr.ocr(temp_img_path, cls=False)
            
            if not result or not result[0]:
                return []
            
            boxes = []
            for line in result[0]:
                if len(line) >= 2:
                    bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    text_info = line[1]
                    text = text_info[0] if isinstance(text_info, (list, tuple)) else str(text_info)
                    score = text_info[1] if isinstance(text_info, (list, tuple)) and len(text_info) > 1 else 1.0
                    
                    boxes.append({
                        'bbox': bbox,
                        'text': text,
                        'score': score
                    })
            
            return boxes
        finally:
            try:
                os.unlink(temp_img_path)
            except Exception:
                pass
    
    def get_bbox_bounds(self, bbox: List[List[float]]) -> Tuple[int, int, int, int]:
        """Convert bbox to (x_min, y_min, x_max, y_max) format
        
        Args:
            bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            
        Returns:
            (x_min, y_min, x_max, y_max)
        """
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        return (
            int(min(x_coords)),
            int(min(y_coords)),
            int(max(x_coords)),
            int(max(y_coords))
        )
