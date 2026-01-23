"""Short prompts for field-specific extraction"""
from __future__ import annotations

from typing import Dict, Any
from pathlib import Path


class FieldExtractorPrompts:
    """Short prompts for extracting individual fields"""
    
    PROMPTS = {
        'vencimento': """Analise esta imagem e extraia APENAS a data de vencimento.

RETORNE APENAS UM JSON VÁLIDO:
{
  "vencimento": "DD/MM/AAAA"
}

REGRAS:
- Formato: "DD/MM/AAAA" (ex: "15/01/2024")
- Se não encontrar, retorne: {"vencimento": ""}""",

        'mes_referencia': """Analise esta imagem e extraia APENAS o mês de referência.

RETORNE APENAS UM JSON VÁLIDO:
{
  "mes_referencia": "MM/AAAA"
}

REGRAS:
- Formato: "MM/AAAA" (ex: "01/2024", "10/2025")
- Se aparecer formato abreviado (ex: "OUT/2025"), converta:
  - JAN=01, FEV=02, MAR=03, ABR=04, MAI=05, JUN=06
  - JUL=07, AGO=08, SET=09, OUT=10, NOV=11, DEZ=12
- Se não encontrar, retorne: {"mes_referencia": ""}""",

        'valor_fatura': """Analise esta imagem e extraia APENAS o valor total da fatura.

RETORNE APENAS UM JSON VÁLIDO:
{
  "valor_fatura": 123.45
}

REGRAS:
- Número float (ex: 123.45, 140.54)
- Remova "R$" e separadores de milhar
- Use ponto como separador decimal
- Se não encontrar, retorne: {"valor_fatura": 0.0}""",

        'aliquota_icms': """Analise esta imagem e extraia APENAS a alíquota de ICMS.

RETORNE APENAS UM JSON VÁLIDO:
{
  "aliquota_icms": 19.0
}

REGRAS:
- Número float (ex: 18.0, 19.0, 22.0)
- Procure por "%" ou "ICMS"
- Se não encontrar, retorne: {"aliquota_icms": null}""",

        'cod_cliente': """Analise esta imagem e extraia APENAS o código do cliente.

RETORNE APENAS UM JSON VÁLIDO:
{
  "cod_cliente": "12345678"
}

REGRAS:
- String com números (ex: "12345678", "112326427")
- Procure por "Código Cliente", "Parceiro de Negócio", etc.
- Se não encontrar, retorne: {"cod_cliente": ""}""",

        'num_instalacao': """Analise esta imagem e extraia APENAS o número da instalação.

RETORNE APENAS UM JSON VÁLIDO:
{
  "num_instalacao": "30052610"
}

REGRAS:
- String com números (ex: "30052610", "10031843326")
- Procure por "Instalação", "Unidade Consumidora", etc.
- Se não encontrar, retorne: {"num_instalacao": ""}""",
    }
    
    @classmethod
    def get_prompt(cls, field: str) -> str:
        """Get prompt for a specific field
        
        Args:
            field: Field name
            
        Returns:
            Prompt string
        """
        return cls.PROMPTS.get(field, "")
