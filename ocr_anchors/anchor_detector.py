"""Anchor detection for finding keywords in OCR results"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image


class AnchorDetector:
    """Detects anchor keywords in OCR results"""
    
    # Mapeamento de campos para palavras-chave de busca
    FIELD_ANCHORS = {
        'vencimento': [
            r'vencimento',
            r'vencto',
            r'venc\.',
            r'venc',
            r'data.*vencimento',
        ],
        'mes_referencia': [
            r'mês',
            r'mes',
            r'referência',
            r'referencia',
            r'ref\.',
            r'ref',
            r'conta.*mês',
        ],
        'valor_fatura': [
            r'total.*pagar',
            r'total.*a.*pagar',
            r'valor.*fatura',
            r'valor.*total',
            r'r\$\s*\d',
            r'valor',
        ],
        'aliquota_icms': [
            r'icms',
            r'alíquota',
            r'aliquota',
            r'%',
        ],
        'cod_cliente': [
            r'código.*cliente',
            r'codigo.*cliente',
            r'cod.*cliente',
            r'parceiro.*negócio',
            r'parceiro.*negocio',
            r'cliente',
        ],
        'num_instalacao': [
            r'instalação',
            r'instalacao',
            r'unidade.*consumidora',
            r'nº.*instalação',
            r'n\.º.*instalação',
        ],
    }
    
    def __init__(self, case_sensitive: bool = False):
        """Initialize anchor detector
        
        Args:
            case_sensitive: Whether to match case sensitively
        """
        self.case_sensitive = case_sensitive
        self.flags = 0 if case_sensitive else re.IGNORECASE
    
    def find_anchors(
        self, 
        ocr_results: List[Dict[str, Any]], 
        field: str
    ) -> List[Dict[str, Any]]:
        """Find anchor matches for a specific field
        
        Args:
            ocr_results: List of OCR results with 'bbox', 'text', 'score'
            field: Field name to search for
            
        Returns:
            List of matching OCR results
        """
        if field not in self.FIELD_ANCHORS:
            return []
        
        patterns = self.FIELD_ANCHORS[field]
        matches = []
        
        for result in ocr_results:
            text = result['text']
            for pattern in patterns:
                if re.search(pattern, text, flags=self.flags):
                    matches.append(result)
                    break  # Found a match, no need to check other patterns
        
        return matches
    
    def find_best_anchor(
        self,
        ocr_results: List[Dict[str, Any]],
        field: str,
        img_width: int,
        img_height: int
    ) -> Optional[Dict[str, Any]]:
        """Find the best anchor match for a field
        
        Prioritizes:
        1. Higher confidence score
        2. Position (prefers top-left for most fields)
        
        Args:
            ocr_results: List of OCR results
            field: Field name
            img_width: Image width
            img_height: Image height
            
        Returns:
            Best matching OCR result or None
        """
        matches = self.find_anchors(ocr_results, field)
        
        if not matches:
            return None
        
        # Sort by score (descending), then by position
        def score_match(match: Dict[str, Any]) -> Tuple[float, float]:
            score = match.get('score', 0.0)
            bbox = match['bbox']
            # Get center position (prefer top-left)
            x_center = sum(p[0] for p in bbox) / len(bbox)
            y_center = sum(p[1] for p in bbox) / len(bbox)
            # Normalize position (0,0 is top-left)
            pos_score = (y_center / img_height) * 0.1 + (x_center / img_width) * 0.01
            return (-score, pos_score)  # Negative for descending sort
        
        matches.sort(key=score_match)
        return matches[0]
