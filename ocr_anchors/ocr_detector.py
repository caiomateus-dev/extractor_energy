"""OCR detector using PaddleOCR for text detection and bounding boxes"""
from __future__ import annotations

import re
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image
import numpy as np

try:
    from paddleocr import PaddleOCR
    _HAS_PADDLEOCR = True
except ImportError:
    _HAS_PADDLEOCR = False


class OCRDetector:
    """Detects text and bounding boxes using PaddleOCR"""
    
    def __init__(self, lang: str = "pt"):
        """Initialize PaddleOCR detector
        
        Args:
            lang: Language code ('pt' for Portuguese, 'en' for English)
        """
        if not _HAS_PADDLEOCR:
            raise RuntimeError("PaddleOCR not installed. Install with: pip install paddleocr")
        
        # Initialize OCR with detection and recognition
        # use_angle_cls=False for faster processing (we assume upright text)
        self.ocr = PaddleOCR(
            use_angle_cls=False,
            lang=lang,
            show_log=False
        )
    
    def detect_text_boxes(self, img: Image.Image) -> List[Dict[str, Any]]:
        """Detect text bounding boxes and extract text from image
        
        Args:
            img: PIL Image
            
        Returns:
            List of dicts with keys: 'bbox', 'text', 'score'
            bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        # Convert PIL to numpy array
        img_array = np.array(img.convert('RGB'))
        
        # Run OCR
        result = self.ocr.ocr(img_array, cls=False)
        
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
