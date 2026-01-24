"""Normalization and contract validation (month, CEP, ensure_contract)."""

from __future__ import annotations

import re
from typing import Any, Dict

from .logging_metrics import log
from .prompts import key_normalize


def to_float(x: Any, default: float) -> float:
    try:
        if isinstance(x, str):
            s = x.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            return float(s)
        return float(x)
    except Exception:
        return default


def normalize_month_reference(mes_ref: str) -> str:
    """Converte mes_referencia (OUT/2025) -> (10/2025)."""
    if not mes_ref or not isinstance(mes_ref, str):
        return mes_ref
    mes_ref = mes_ref.strip().upper()
    month_map = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
        "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
        "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12",
    }
    if re.match(r"^\d{2}/\d{4}$", mes_ref):
        return mes_ref
    parts = mes_ref.split("/")
    if len(parts) != 2:
        return mes_ref
    mes_abrev = parts[0].strip()
    ano = parts[1].strip()
    if len(ano) == 2:
        ai = int(ano)
        ano = f"20{ai:02d}" if ai <= 50 else f"19{ai:02d}"
    if mes_abrev in month_map:
        return f"{month_map[mes_abrev]}/{ano}"
    return mes_ref


def normalize_cep(cep: str) -> str:
    """Normaliza CEP para XX.XXX-XXX."""
    if not cep or not isinstance(cep, str):
        return cep
    c = re.sub(r"[^\d]", "", cep.strip())
    if len(c) == 8:
        return f"{c[:2]}.{c[2:5]}-{c[5:]}"
    return cep


def ensure_contract(
    payload: Dict[str, Any],
    concessionaria_input: str,
    uf: str = "",
) -> Dict[str, Any]:
    """Preenche template, normaliza campos, aplica regras por concessionária."""
    template: Dict[str, Any] = {
        "cod_cliente": "",
        "conta_contrato": "",
        "complemento": "",
        "distribuidora": "",
        "num_instalacao": "",
        "classificacao": "",
        "tipo_instalacao": "",
        "tensao_nominal": "",
        "alta_tensao": False,
        "mes_referencia": "",
        "valor_fatura": 0.0,
        "vencimento": "",
        "proximo_leitura": "",
        "aliquota_icms": None,
        "baixa_renda": False,
        "energia_ativa_injetada": False,
        "energia_reativa": False,
        "orgao_publico": False,
        "parcelamentos": False,
        "tarifa_branca": False,
        "ths_verde": False,
        "faturas_venc": False,
        "valores_em_aberto": [],
        "nome_cliente": "",
        "rua": "",
        "numero": "",
        "bairro": "",
        "cidade": "",
        "estado": "",
        "cep": "",
        "consumo_lista": [],
    }
    out = dict(template)
    for k in template:
        if k in payload:
            out[k] = payload[k]

    if not str(out.get("distribuidora", "")).strip():
        out["distribuidora"] = concessionaria_input
    mes_ref = str(out.get("mes_referencia", "")).strip()
    if mes_ref:
        out["mes_referencia"] = normalize_month_reference(mes_ref)
    cep = str(out.get("cep", "")).strip()
    if cep:
        out["cep"] = normalize_cep(cep)
    out["valor_fatura"] = to_float(out["valor_fatura"], 0.0)
    if out["aliquota_icms"] is not None:
        try:
            out["aliquota_icms"] = to_float(out["aliquota_icms"], 0.0)
        except Exception:
            out["aliquota_icms"] = None
    if not isinstance(out["valores_em_aberto"], list):
        out["valores_em_aberto"] = []
    cleaned_vo = []
    for item in out["valores_em_aberto"]:
        if not isinstance(item, dict):
            continue
        cleaned_vo.append({
            "mes_ano": str(item.get("mes_ano", "")).strip(),
            "valor": to_float(item.get("valor", 0.0), 0.0),
        })
    out["valores_em_aberto"] = cleaned_vo

    for b in [
        "alta_tensao", "baixa_renda", "energia_ativa_injetada", "energia_reativa",
        "orgao_publico", "parcelamentos", "tarifa_branca", "ths_verde", "faturas_venc",
    ]:
        out[b] = bool(out[b])

    if not isinstance(out.get("consumo_lista"), list):
        out["consumo_lista"] = []
    consumo_ok = []
    for item in out["consumo_lista"]:
        if not isinstance(item, dict):
            continue
        consumo = item.get("consumo")
        try:
            c = int(consumo) if consumo is not None else 0
        except (ValueError, TypeError):
            c = 0
        consumo_ok.append({"mes_ano": str(item.get("mes_ano", "")).strip(), "consumo": c})
    out["consumo_lista"] = consumo_ok

    ckey = key_normalize(concessionaria_input)
    ufkey = key_normalize(uf)
    if ckey == "equatorial" and ufkey == "go":
        out["conta_contrato"] = None
        log(f"[validation] conta_contrato = null para {concessionaria_input}/{uf}")
    estado = str(out.get("estado", "")).strip().upper()
    uf_up = uf.strip().upper()
    if estado and uf_up:
        if estado != uf_up:
            log(f"[validation] estado '{estado}' != UF '{uf_up}', corrigindo")
            out["estado"] = uf_up
        else:
            out["estado"] = estado
    elif uf_up:
        out["estado"] = uf_up
        log(f"[validation] estado ausente, usando UF {uf_up}")

    return out
