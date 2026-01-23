"""Tiling fallback for when anchor detection fails"""
from __future__ import annotations

from typing import List, Tuple, Optional
from PIL import Image
import math


class TilingFallback:
    """Generates image tiles for fallback extraction"""
    
    def __init__(
        self,
        tile_size: Tuple[int, int] = (400, 400),
        overlap: int = 50
    ):
        """Initialize tiling fallback
        
        Args:
            tile_size: Size of each tile (width, height)
            overlap: Overlap between tiles in pixels
        """
        self.tile_size = tile_size
        self.overlap = overlap
    
    def generate_tiles(
        self,
        img: Image.Image,
        grid_size: Tuple[int, int] = (2, 2)
    ) -> List[Tuple[Image.Image, Tuple[int, int]]]:
        """Generate tiles from image
        
        Args:
            img: Source image
            grid_size: Grid size (cols, rows)
            
        Returns:
            List of (tile_image, (col, row)) tuples
        """
        img_width, img_height = img.size
        cols, rows = grid_size
        
        # Calculate step size with overlap
        step_x = (img_width - self.overlap) // cols
        step_y = (img_height - self.overlap) // rows
        
        tiles = []
        for row in range(rows):
            for col in range(cols):
                x_min = col * step_x
                y_min = row * step_y
                x_max = min(img_width, x_min + self.tile_size[0])
                y_max = min(img_height, y_min + self.tile_size[1])
                
                # Ensure minimum size
                if x_max - x_min < 50 or y_max - y_min < 50:
                    continue
                
                try:
                    tile = img.crop((x_min, y_min, x_max, y_max))
                    tiles.append((tile, (col, row)))
                except Exception:
                    continue
        
        return tiles
    
    def generate_adaptive_tiles(
        self,
        img: Image.Image,
        max_tiles: int = 9
    ) -> List[Tuple[Image.Image, Tuple[int, int]]]:
        """Generate adaptive tiles based on image size
        
        Args:
            img: Source image
            max_tiles: Maximum number of tiles
            
        Returns:
            List of (tile_image, (col, row)) tuples
        """
        img_width, img_height = img.size
        
        # Calculate grid size based on image dimensions
        aspect_ratio = img_width / img_height
        
        if aspect_ratio > 1.5:  # Wide image
            cols = min(3, int(math.sqrt(max_tiles * aspect_ratio)))
            rows = min(3, int(math.sqrt(max_tiles / aspect_ratio)))
        else:  # Tall or square image
            rows = min(3, int(math.sqrt(max_tiles / aspect_ratio)))
            cols = min(3, int(math.sqrt(max_tiles * aspect_ratio)))
        
        return self.generate_tiles(img, (cols, rows))
