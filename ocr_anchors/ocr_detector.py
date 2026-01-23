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
            # Initialize OCR with same config as ocr.py
            import os
            os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
            os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
            
            self.ocr = PaddleOCR(
                ocr_version="PP-OCRv5",
                lang=lang,
                use_doc_unwarping=False,
                use_doc_orientation_classify=False,
                use_textline_orientation=True,
                text_det_limit_type="max",
                text_det_limit_side_len=960,  # Reduzido de 1536 para acelerar (menos qualidade mas mais rápido)
                text_recognition_batch_size=8,  # Batch processing para acelerar
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
        # Convert PIL Image to BGR numpy array (same as ocr.py)
        img_rgb = img.convert('RGB')
        rgb_array = np.array(img_rgb)
        # Convert RGB to BGR (PaddleOCR expects BGR)
        bgr_array = rgb_array[:, :, ::-1].copy()
        
        # Use predict() method with BGR array (same as ocr.py)
        pred_kwargs = {
            "use_doc_unwarping": False,
            "use_doc_orientation_classify": False,
            "use_textline_orientation": True,
        }
        pred = self.ocr.predict(bgr_array, **pred_kwargs)
        
        boxes = []
        
        # Handle new format: list[dict] with rec_texts + rec_polys
        if isinstance(pred, list) and pred and isinstance(pred[0], dict):
            for page in pred:
                texts = page.get("rec_texts") or []
                polys = page.get("rec_polys") or []
                for text, poly in zip(texts, polys):
                    if not text:
                        continue
                    # Convert poly to bbox format
                    arr = np.asarray(poly)
                    if arr.shape != (4, 2):
                        arr = arr.reshape(4, 2)
                    bbox = [[int(x), int(y)] for x, y in arr.tolist()]
                    boxes.append({
                        'bbox': bbox,
                        'text': str(text),
                        'score': 1.0  # New format doesn't provide score per item
                    })
            return boxes
        
        # Handle legacy format: list[list[[poly, (text, score)]]]
        if isinstance(pred, list):
            for line in pred:
                if not isinstance(line, (list, tuple)) or len(line) < 2:
                    continue
                poly, rec = line[0], line[1]
                text = rec[0] if isinstance(rec, (list, tuple)) and rec else ""
                score = rec[1] if isinstance(rec, (list, tuple)) and len(rec) > 1 else 1.0
                if not text:
                    continue
                boxes.append({
                    'bbox': poly,
                    'text': str(text),
                    'score': float(score) if score else 1.0
                })
        
        return boxes
    
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
