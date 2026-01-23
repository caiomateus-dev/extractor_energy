"""Generate crops around anchor points"""
from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any
from PIL import Image
import numpy as np


class CropGenerator:
    """Generates image crops around anchor points"""
    
    def __init__(
        self,
        padding_x: int = 50,
        padding_y: int = 30,
        min_crop_size: Tuple[int, int] = (100, 50),
        max_crop_size: Tuple[int, int] = (800, 400)
    ):
        """Initialize crop generator
        
        Args:
            padding_x: Horizontal padding around anchor
            padding_y: Vertical padding around anchor
            min_crop_size: Minimum crop size (width, height)
            max_crop_size: Maximum crop size (width, height)
        """
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.min_crop_size = min_crop_size
        self.max_crop_size = max_crop_size
    
    def get_bbox_bounds(self, bbox: List[List[float]]) -> Tuple[int, int, int, int]:
        """Convert bbox to (x_min, y_min, x_max, y_max) format"""
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        return (
            int(min(x_coords)),
            int(min(y_coords)),
            int(max(x_coords)),
            int(max(y_coords))
        )
    
    def generate_crop(
        self,
        img: Image.Image,
        anchor_bbox: List[List[float]],
        context_lines: int = 2
    ) -> Optional[Image.Image]:
        """Generate crop around anchor with context
        
        Args:
            img: Source image
            anchor_bbox: Bounding box of anchor [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            context_lines: Number of text lines to include above/below
            
        Returns:
            Cropped image or None if crop is invalid
        """
        img_width, img_height = img.size
        
        # Get anchor bounds
        x_min, y_min, x_max, y_max = self.get_bbox_bounds(anchor_bbox)
        
        # Estimate line height (approximate from bbox height)
        line_height = max(y_max - y_min, 20)
        
        # Expand with padding and context
        crop_x_min = max(0, x_min - self.padding_x)
        crop_y_min = max(0, y_min - self.padding_y - (context_lines * line_height))
        crop_x_max = min(img_width, x_max + self.padding_x)
        crop_y_max = min(img_height, y_max + self.padding_y + (context_lines * line_height))
        
        # Ensure minimum size
        crop_width = crop_x_max - crop_x_min
        crop_height = crop_y_max - crop_y_min
        
        if crop_width < self.min_crop_size[0]:
            center_x = (crop_x_min + crop_x_max) // 2
            crop_x_min = max(0, center_x - self.min_crop_size[0] // 2)
            crop_x_max = min(img_width, crop_x_min + self.min_crop_size[0])
        
        if crop_height < self.min_crop_size[1]:
            center_y = (crop_y_min + crop_y_max) // 2
            crop_y_min = max(0, center_y - self.min_crop_size[1] // 2)
            crop_y_max = min(img_height, crop_y_min + self.min_crop_size[1])
        
        # Limit maximum size
        crop_width = crop_x_max - crop_x_min
        crop_height = crop_y_max - crop_y_min
        
        if crop_width > self.max_crop_size[0]:
            center_x = (crop_x_min + crop_x_max) // 2
            crop_x_min = center_x - self.max_crop_size[0] // 2
            crop_x_max = crop_x_min + self.max_crop_size[0]
        
        if crop_height > self.max_crop_size[1]:
            center_y = (crop_y_min + crop_y_max) // 2
            crop_y_min = center_y - self.max_crop_size[1] // 2
            crop_y_max = crop_y_min + self.max_crop_size[1]
        
        # Ensure bounds are within image
        crop_x_min = max(0, crop_x_min)
        crop_y_min = max(0, crop_y_min)
        crop_x_max = min(img_width, crop_x_max)
        crop_y_max = min(img_height, crop_y_max)
        
        # Crop image
        try:
            crop = img.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
            return crop
        except Exception:
            return None
    
    def generate_multiple_crops(
        self,
        img: Image.Image,
        anchors: List[Dict[str, Any]]
    ) -> Dict[str, Optional[Image.Image]]:
        """Generate crops for multiple anchors
        
        Args:
            img: Source image
            anchors: List of anchor dicts with 'field' and 'bbox' keys
            
        Returns:
            Dict mapping field names to cropped images
        """
        crops = {}
        for anchor in anchors:
            field = anchor.get('field')
            bbox = anchor.get('bbox')
            if field and bbox:
                crop = self.generate_crop(img, bbox)
                crops[field] = crop
        return crops
