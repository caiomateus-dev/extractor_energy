from __future__ import annotations

import asyncio
import gc
import io
import json
import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from importlib.util import find_spec
from typing import Any, Dict, Optional, Tuple
import re

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from config import settings

# Importa detecção de objetos para recortes
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from detectors.object_detection import ObjectDetection
    _HAS_OBJECT_DETECTION = True
except ImportError as e:
    _HAS_OBJECT_DETECTION = False
    print(f"[boot] object_detection não disponível - recortes desabilitados: {e}", flush=True)

_HAS_MLX_VLM = find_spec("mlx_vlm") is not None
if _HAS_MLX_VLM:
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config


app = FastAPI(title="Energy Extractor (MLX-VLM + Qwen2.5-VL)")

PROMPTS_DIR = Path(settings.prompts_dir).resolve()


def log(msg: str) -> None:
    print(msg, flush=True)


def _key(s: str) -> str:
    """
    Normaliza chaves vindas do input (ex: "CEMIG-D" -> "cemig-d") sem regex.
    Mantém apenas [a-z0-9] e converte separadores em "-".
    """
    s = s.strip().lower()
    out: list[str] = []
    last_sep = True
    for ch in s:
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
            last_sep = False
            continue
        if not last_sep:
            out.append("-")
            last_sep = True
    if out and out[-1] == "-":
        out.pop()
    return "".join(out)


_PROMPT_MAP_CACHE: dict[str, Any] | None = None
_PROMPT_MAP_MTIME_NS: int | None = None


def _load_prompt_map() -> dict[str, Any]:
    global _PROMPT_MAP_CACHE, _PROMPT_MAP_MTIME_NS

    path = PROMPTS_DIR / "mapper.json"
    if not path.exists():
        return {}

    st = path.stat()
    mtime_ns = getattr(st, "st_mtime_ns", None) or int(st.st_mtime * 1e9)
    if _PROMPT_MAP_CACHE is not None and _PROMPT_MAP_MTIME_NS == mtime_ns:
        return _PROMPT_MAP_CACHE

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Formato inválido em {path.as_posix()}: esperado um JSON object.")

    _PROMPT_MAP_CACHE = data
    _PROMPT_MAP_MTIME_NS = mtime_ns
    return data


def _format_bytes(n: int | None) -> str:
    if n is None:
        return "n/a"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f}{u}"
        x /= 1024
    return f"{x:.1f}{units[-1]}"


def _process_rss_bytes() -> int | None:
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(rss) if os.uname().sysname == "Darwin" else int(rss) * 1024
    except Exception:
        return None


def _system_memory_total_available_bytes() -> tuple[int | None, int | None]:
    try:
        if os.uname().sysname == "Linux":
            total = available = None
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total = int(line.split()[1]) * 1024
                    elif line.startswith("MemAvailable:"):
                        available = int(line.split()[1]) * 1024
            return total, available
    except Exception:
        pass

    try:
        if os.uname().sysname == "Darwin":
            import subprocess

            total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
            vm = subprocess.check_output(["vm_stat"], text=True)
            page_size = 4096
            m = re.search(r"page size of (\\d+) bytes", vm)
            if m:
                page_size = int(m.group(1))

            pages = {}
            for line in vm.splitlines():
                mm = re.match(r"^Pages (.+?):\\s+(\\d+)\\.$", line.strip())
                if mm:
                    pages[mm.group(1)] = int(mm.group(2))

            available_pages = (
                pages.get("free", 0)
                + pages.get("inactive", 0)
                + pages.get("speculative", 0)
            )
            available = available_pages * page_size
            return total, available
    except Exception:
        pass

    return None, None


def _metal_memory_bytes() -> Dict[str, int]:
    """Retorna dict vazio - API mlx.metal foi removida (deprecated)"""
    return {}


def _clear_metal_cache() -> None:
    """
    Limpa o cache do Metal/MLX após inferência para liberar memória GPU.
    Usa mx.clear_cache() que é a API recomendada (mx.metal.clear_cache está deprecado).
    """
    try:
        import mlx.core as mx  # type: ignore
        
        # Limpa cache usando a API recomendada (não deprecada)
        if hasattr(mx, "clear_cache"):
            try:
                mx.clear_cache()
            except Exception:
                pass
        
        # Força avaliação de arrays pendentes se o modelo estiver carregado
        # Isso ajuda a liberar memória de arrays intermediários
        global MODEL
        if MODEL is not None and hasattr(MODEL, "parameters"):
            try:
                # Avalia parâmetros do modelo para sincronizar operações
                params = MODEL.parameters()
                if isinstance(params, dict):
                    # Avalia todos os parâmetros do modelo
                    mx.eval(list(params.values()))
            except Exception:
                pass
    except Exception:
        pass


def _log_system_metrics(tag: str) -> None:
    rss = _process_rss_bytes()
    total, avail = _system_memory_total_available_bytes()
    log(
        f"{tag} rss={_format_bytes(rss)} "
        f"ram_total={_format_bytes(total)} ram_avail={_format_bytes(avail)}"
    )


MODEL = PROCESSOR = CONFIG = None
OBJECT_DETECTOR = None

if not _HAS_MLX_VLM:
    log(
        "[boot] missing dependency: mlx-vlm (module: mlx_vlm). "
        "Use the project venv (e.g. `uv sync` then `uv run uvicorn main:app --reload`) "
        f"or install it into {sys.executable}."
    )
else:
    log(f"[boot] loading model: {settings.model_id}")
    MODEL, PROCESSOR = load(settings.model_id)
    CONFIG = load_config(settings.model_id)
    log("[boot] model loaded")
    _log_system_metrics("[boot][mem]")

# Inicializa detector de objetos para recortes (lazy loading - não pré-carrega modelos)
if _HAS_OBJECT_DETECTION:
    try:
        t_yolo_start = time.time()
        OBJECT_DETECTOR = ObjectDetection()
        # Não pré-carrega modelos YOLO aqui para evitar demora no boot
        # Os modelos serão carregados na primeira requisição (lazy loading)
        t_yolo_end = time.time()
        log(f"[boot] object detector inicializado em {(t_yolo_end - t_yolo_start)*1000:.1f}ms")
    except Exception as e:
        log(f"[boot] erro ao carregar object detector: {e}")
        OBJECT_DETECTOR = None


# Semáforo para controlar concorrência dentro do mesmo worker
# Com múltiplos workers, cada worker tem seu próprio modelo e processa independentemente
_GATE = asyncio.Semaphore(settings.max_concurrency)


def _read_prompt(concessionaria: str, uf: str) -> str:
    base_path = PROMPTS_DIR / "base.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")

    base = base_path.read_text(encoding="utf-8").strip()

    mapper = _load_prompt_map()
    prompts = mapper.get("prompts", {}) if isinstance(mapper.get("prompts", {}), dict) else {}
    aliases = mapper.get("aliases", {}) if isinstance(mapper.get("aliases", {}), dict) else {}

    concessionaria_key = _key(concessionaria)
    aliased = aliases.get(concessionaria_key)
    if isinstance(aliased, str) and aliased.strip():
        concessionaria_key = _key(aliased)
    uf_key = _key(uf)

    spec_filename: str | None = None
    by_uf = prompts.get(concessionaria_key)
    if isinstance(by_uf, dict):
        v = by_uf.get(uf_key) or by_uf.get("*")
        if isinstance(v, str) and v.strip():
            spec_filename = v.strip()
    elif isinstance(by_uf, str) and by_uf.strip():
        spec_filename = by_uf.strip()

    spec = ""
    if spec_filename:
        spec_path = PROMPTS_DIR / spec_filename
        if not spec_path.exists():
            raise RuntimeError(
                f"Prompt mapeado não encontrado: {spec_path.as_posix()} "
                f"(concessionaria={concessionaria_key}, uf={uf_key})"
            )
        spec = spec_path.read_text(encoding="utf-8").strip()

    return base + ("\n\n" + spec if spec else "")


def _save_image_temp(img: Image.Image) -> str:
    """Salva imagem PIL em arquivo temporário para uso com modelos YOLO"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    img.save(temp_path, format='PNG')
    return temp_path


def _load_image(raw: bytes) -> Image.Image:
    """
    Carrega e processa imagem de forma eficiente em memória.
    Redimensiona AGressivamente se necessário para evitar alocações excessivas no Metal.
    
    IMPORTANTE: Imagens grandes podem causar alocações de dezenas de GB no Metal
    durante o processamento do modelo VLM. Redimensionamos ANTES de processar.
    """
    # Carrega imagem diretamente do bytes
    bio = io.BytesIO(raw)
    try:
        img = Image.open(bio).convert("RGB")
        w, h = img.size
        pixels = w * h
        
        # Log do tamanho original para debug
        if pixels > settings.max_pixels:
            log(f"[img] imagem grande detectada: {w}x{h} ({pixels:,} pixels) - redimensionando")
        
        # Redimensiona ANTES de criar cópia para economizar memória
        if pixels > settings.max_pixels:
            scale = (settings.max_pixels / float(pixels)) ** 0.5
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            log(f"[img] redimensionada para: {nw}x{nh} ({nw*nh:,} pixels)")
        
        # Cria cópia final (já redimensionada se necessário)
        img_copy = img.copy()
        img.close()  # Fecha a imagem original
    finally:
        bio.close()  # Fecha o BytesIO
    
    return img_copy


def _extract_json(text: str) -> Dict[str, Any]:
    """Extrai JSON do texto, removendo mensagens de deprecação e outros textos extras"""
    text = text.strip()
    
    # Remove linhas com mensagens de deprecação ou avisos
    lines = text.split('\n')
    filtered_lines = []
    skip_until_json = False
    for line in lines:
        line_lower = line.lower()
        # Pula linhas de deprecação, avisos, ou separadores
        if any(x in line_lower for x in ['deprecated', 'calling', 'python -m', '==========', 'files:', 'prompt:']):
            skip_until_json = True
            continue
        # Se encontrou uma chave JSON, para de pular
        if '{' in line or '[' in line:
            skip_until_json = False
        if not skip_until_json:
            filtered_lines.append(line)
    
    text = '\n'.join(filtered_lines).strip()
    
    # Tenta encontrar JSON válido
    # Primeiro tenta objeto JSON completo
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    
    # Procura por objeto JSON no texto
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    
    # Procura por qualquer JSON válido (mais permissivo)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        json_str = m.group(0)
        # Tenta limpar vírgulas finais e outros problemas comuns
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Nenhum JSON válido encontrado na resposta. Erro: {e}. Texto: {text[:500]}")
    
    raise ValueError(f"Nenhum JSON encontrado na resposta do modelo. Texto: {text[:500]}")


def _to_float(x: Any, default: float) -> float:
    try:
        if isinstance(x, str):
            s = x.replace("R$", "").replace(" ", "")
            s = s.replace(".", "").replace(",", ".")
            return float(s)
        return float(x)
    except Exception:
        return default


def _normalize_month_reference(mes_ref: str) -> str:
    """Converte mes_referencia de formato abreviado (OUT/2025) para numérico (10/2025)"""
    if not mes_ref or not isinstance(mes_ref, str):
        return mes_ref
    
    mes_ref = mes_ref.strip().upper()
    
    # Mapeamento de meses abreviados para numéricos
    month_map = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
        "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
        "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
    }
    
    # Verifica se já está no formato numérico (MM/AAAA)
    if re.match(r'^\d{2}/\d{4}$', mes_ref):
        return mes_ref
    
    # Tenta converter formato abreviado (OUT/2025 ou OUT/25)
    parts = mes_ref.split("/")
    if len(parts) == 2:
        mes_abrev = parts[0].strip()
        ano = parts[1].strip()
        
        # Converte ano de 2 dígitos para 4 dígitos se necessário
        if len(ano) == 2:
            ano_int = int(ano)
            # Assume que anos 00-50 são 2000-2050, e 51-99 são 1951-1999
            if ano_int <= 50:
                ano = f"20{ano:02d}"
            else:
                ano = f"19{ano:02d}"
        
        # Converte mês abreviado para numérico
        if mes_abrev in month_map:
            return f"{month_map[mes_abrev]}/{ano}"
    
    # Se não conseguir converter, retorna o original
    return mes_ref


def _normalize_cep(cep: str) -> str:
    """Normaliza CEP para o formato XX.XXX-XXX"""
    if not cep or not isinstance(cep, str):
        return cep
    
    # Remove todos os caracteres não numéricos
    cep_clean = re.sub(r'[^\d]', '', cep.strip())
    
    # Verifica se tem 8 dígitos
    if len(cep_clean) == 8:
        return f"{cep_clean[:2]}.{cep_clean[2:5]}-{cep_clean[5:]}"
    
    # Se não tiver 8 dígitos, retorna o original
    return cep


def _ensure_contract(payload: Dict[str, Any], concessionaria_input: str) -> Dict[str, Any]:
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
        "complemento": "",
        "bairro": "",
        "cidade": "",
        "estado": "",
        "cep": "",
        "consumo_lista": [],
    }

    out = dict(template)
    for k in template.keys():
        if k in payload:
            out[k] = payload[k]

    if not str(out.get("distribuidora", "")).strip():
        out["distribuidora"] = concessionaria_input

    # Normaliza mes_referencia para formato numérico
    mes_ref = str(out.get("mes_referencia", "")).strip()
    if mes_ref:
        out["mes_referencia"] = _normalize_month_reference(mes_ref)

    # Normaliza CEP para formato XX.XXX-XXX
    cep = str(out.get("cep", "")).strip()
    if cep:
        out["cep"] = _normalize_cep(cep)

    out["valor_fatura"] = _to_float(out["valor_fatura"], 0.0)

    if out["aliquota_icms"] is not None:
        try:
            out["aliquota_icms"] = _to_float(out["aliquota_icms"], 0.0)
        except Exception:
            out["aliquota_icms"] = None

    if not isinstance(out["valores_em_aberto"], list):
        out["valores_em_aberto"] = []

    for b in [
        "alta_tensao", "baixa_renda", "energia_ativa_injetada", "energia_reativa",
        "orgao_publico", "parcelamentos", "tarifa_branca", "ths_verde", "faturas_venc",
    ]:
        out[b] = bool(out[b])

    cleaned = []
    for item in out["valores_em_aberto"]:
        if not isinstance(item, dict):
            continue
        mes_ano = str(item.get("mes_ano", "")).strip()
        valor = _to_float(item.get("valor", 0.0), 0.0)
        cleaned.append({"mes_ano": mes_ano, "valor": valor})
    out["valores_em_aberto"] = cleaned

    # Valida consumo_lista
    if not isinstance(out.get("consumo_lista"), list):
        out["consumo_lista"] = []
    consumo_cleaned = []
    for item in out["consumo_lista"]:
        if not isinstance(item, dict):
            continue
        mes_ano = str(item.get("mes_ano", "")).strip()
        consumo = item.get("consumo")
        try:
            consumo_int = int(consumo) if consumo is not None else 0
        except (ValueError, TypeError):
            consumo_int = 0
        consumo_cleaned.append({"mes_ano": mes_ano, "consumo": consumo_int})
    out["consumo_lista"] = consumo_cleaned

    return out


def _read_customer_address_prompt(concessionaria: str = "", uf: str = "") -> str:
    """Carrega prompt específico para extração de nome do cliente e endereço"""
    # Carrega regras específicas da concessionária se disponível
    spec_prompt = ""
    try:
        mapper = _load_prompt_map()
        prompts = mapper.get("prompts", {}) if isinstance(mapper.get("prompts", {}), dict) else {}
        aliases = mapper.get("aliases", {}) if isinstance(mapper.get("aliases", {}), dict) else {}
        
        concessionaria_key = _key(concessionaria)
        aliased = aliases.get(concessionaria_key)
        if isinstance(aliased, str) and aliased.strip():
            concessionaria_key = _key(aliased)
        uf_key = _key(uf)
        
        spec_filename: str | None = None
        by_uf = prompts.get(concessionaria_key)
        if isinstance(by_uf, dict):
            v = by_uf.get(uf_key) or by_uf.get("*")
            if isinstance(v, str) and v.strip():
                spec_filename = v.strip()
        elif isinstance(by_uf, str) and by_uf.strip():
            spec_filename = by_uf.strip()
        
        if spec_filename:
            spec_path = PROMPTS_DIR / spec_filename
            if spec_path.exists():
                spec_content = spec_path.read_text(encoding="utf-8").strip()
                # Extrai apenas a seção de ENDEREÇO DO CLIENTE
                if "ENDEREÇO DO CLIENTE" in spec_content:
                    start_idx = spec_content.find("ENDEREÇO DO CLIENTE")
                    end_idx = spec_content.find("==========================", start_idx + 1)
                    if end_idx == -1:
                        end_idx = len(spec_content)
                    spec_prompt = spec_content[start_idx:end_idx].strip()
    except Exception:
        pass
    
    base_path = PROMPTS_DIR / "customer_address.md"
    if not base_path.exists():
        raise RuntimeError(f"Arquivo {base_path.as_posix()} não encontrado.")
    
    base_prompt = base_path.read_text(encoding="utf-8").strip()
    
    if spec_prompt:
        return f"""{base_prompt}

REGRAS ESPECÍFICAS DA CONCESSIONÁRIA:
{spec_prompt}"""
    
    return base_prompt


def _read_consumption_prompt() -> str:
    """Carrega prompt específico para extração de consumo médio"""
    path = PROMPTS_DIR / "consumption.md"
    if not path.exists():
        raise RuntimeError(f"Arquivo {path.as_posix()} não encontrado.")
    return path.read_text(encoding="utf-8").strip()


async def _infer_one(img: Image.Image, prompt_text: str) -> str:
    if not _HAS_MLX_VLM:
        raise RuntimeError("Dependência MLX-VLM indisponível para inferência.")

    # Valida tamanho da imagem antes de processar
    w, h = img.size
    pixels = w * h
    if pixels > settings.max_pixels:
        raise ValueError(
            f"Imagem muito grande: {w}x{h} ({pixels:,} pixels). "
            f"Máximo permitido: {settings.max_pixels:,} pixels. "
            f"Redimensione a imagem antes de enviar."
        )
    
    log(f"[infer] processando imagem: {w}x{h} ({pixels:,} pixels)")

    # Salva imagem temporariamente para subprocess
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_prompt_file = None
    try:
        # Converte para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(temp_img.name, format='JPEG', quality=95)
        temp_img_path = temp_img.name
        
        # Para prompts longos, salva em arquivo temporário para evitar problemas com shell
        # O CLI pode ter limitações de tamanho de argumento
        if len(prompt_text) > 8000:  # Limite conservador para argumentos de shell
            temp_prompt_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt", encoding='utf-8')
            temp_prompt_file.write(prompt_text)
            temp_prompt_file.close()
            temp_prompt_path = temp_prompt_file.name
            use_prompt_file = True
        else:
            temp_prompt_path = None
            use_prompt_file = False
    except Exception as e:
        if temp_img:
            try:
                os.unlink(temp_img.name)
            except:
                pass
        raise

    loop = asyncio.get_running_loop()

    def _run() -> str:
        try:
            # Usa subprocess para chamar mlx_vlm.generate como processo separado
            # Isso permite paralelismo real - cada chamada é um processo independente
            # Usa python -m mlx_vlm.generate conforme documentação
            # O CLI formata o prompt automaticamente, então passamos o prompt bruto
            cmd = [
                sys.executable, "-m", "mlx_vlm.generate",
                "--model", settings.model_id,
                "--max-tokens", str(settings.max_tokens),
                "--temperature", str(settings.temperature),
            ]
            
            # Adiciona prompt: direto ou via arquivo
            if use_prompt_file:
                # Lê o prompt do arquivo e passa como argumento (alguns CLIs suportam @file)
                # Mas mlx_vlm.generate não suporta @file, então vamos passar direto mesmo
                # Se o arquivo for muito grande, pode ser necessário outra abordagem
                with open(temp_prompt_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                cmd.extend(["--prompt", prompt_content])
            else:
                cmd.extend(["--prompt", prompt_text])
            
            cmd.extend(["--image", temp_img_path])
            
            log(f"[infer] comando: {' '.join(cmd[:6])} ... --prompt [{len(prompt_text)} chars] --image {temp_img_path}")
            log(f"[infer] prompt (primeiros 300 chars): {prompt_text[:300]}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.request_timeout_s,
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Erro desconhecido no subprocesso"
                log(f"[infer] erro no subprocesso (code {result.returncode}): {error_msg[:500]}")
                raise RuntimeError(f"Falha no processamento: {error_msg[:200]}")
            
            output = result.stdout.strip()
            log(f"[infer] output bruto (tamanho: {len(output)} chars, primeiros 1000 chars): {output[:1000]}")
            log(f"[infer] output bruto (últimos 1000 chars): {output[-1000:]}")
            
            def _find_balanced_json(text: str, start_char: str = '{') -> str | None:
                """Encontra JSON completo com chaves/colchetes balanceados"""
                if start_char == '{':
                    end_char = '}'
                    open_char, close_char = '{', '}'
                else:
                    end_char = ']'
                    open_char, close_char = '[', ']'
                
                start_pos = text.find(start_char)
                if start_pos == -1:
                    return None
                
                depth = 0
                in_string = False
                escape_next = False
                
                for i in range(start_pos, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if in_string:
                        continue
                    
                    if char == open_char:
                        depth += 1
                    elif char == close_char:
                        depth -= 1
                        if depth == 0:
                            return text[start_pos:i+1]
                
                return None
            
            # A resposta real do modelo vem após <|im_start|>assistant
            # Procura por esse marcador e pega tudo depois
            assistant_marker = '<|im_start|>assistant'
            assistant_pos = output.find(assistant_marker)
            
            if assistant_pos >= 0:
                # Pega tudo após o marcador assistant
                response_section = output[assistant_pos + len(assistant_marker):].strip()
                
                # Remove tokens de formatação restantes
                response_section = re.sub(r'<\|[^|]+\|>', '', response_section).strip()
                
                log(f"[infer] seção resposta após assistant (tamanho: {len(response_section)} chars, primeiros 500 chars): {response_section[:500]}")
                
                # Remove delimitadores markdown primeiro (se houver)
                # Isso ajuda a encontrar o JSON real
                cleaned_section = re.sub(r'```json\s*', '', response_section)
                cleaned_section = re.sub(r'\s*```', '', cleaned_section)
                cleaned_section = cleaned_section.strip()
                
                # Tenta encontrar JSON completo com chaves balanceadas
                json_start = cleaned_section.find('{')
                if json_start != -1:
                    log(f"[infer] encontrado {{ na posição {json_start}, tentando extrair JSON balanceado...")
                    balanced_json = _find_balanced_json(cleaned_section[json_start:], '{')
                    if balanced_json:
                        # Valida se o JSON é válido tentando fazer parse
                        try:
                            json.loads(balanced_json)
                            filtered_output = balanced_json
                            log(f"[infer] JSON balanceado válido encontrado (tamanho: {len(balanced_json)} chars)")
                        except json.JSONDecodeError as e:
                            log(f"[infer] AVISO: JSON balanceado não é válido: {e}. Tentando fallback...")
                            # Fallback: tenta encontrar JSON válido de outra forma
                            # Procura pelo último } que fecha o objeto principal
                            last_brace = cleaned_section.rfind('}')
                            if last_brace > json_start:
                                potential_json = cleaned_section[json_start:last_brace+1]
                                try:
                                    json.loads(potential_json)
                                    filtered_output = potential_json
                                    log(f"[infer] JSON válido encontrado via fallback (tamanho: {len(potential_json)} chars)")
                                except json.JSONDecodeError:
                                    filtered_output = balanced_json  # Usa o que encontrou mesmo assim
                            else:
                                filtered_output = balanced_json
                    else:
                        log(f"[infer] AVISO: _find_balanced_json retornou None. Tentando fallback...")
                        # Fallback: procura pelo último } que fecha o objeto
                        last_brace = cleaned_section.rfind('}')
                        if last_brace > json_start:
                            potential_json = cleaned_section[json_start:last_brace+1]
                            try:
                                json.loads(potential_json)
                                filtered_output = potential_json
                                log(f"[infer] JSON válido encontrado via fallback rfind (tamanho: {len(potential_json)} chars)")
                            except json.JSONDecodeError:
                                # Último recurso: tenta lista JSON
                                list_start = cleaned_section.find('[')
                                if list_start != -1:
                                    balanced_list = _find_balanced_json(cleaned_section[list_start:], '[')
                                    if balanced_list:
                                        filtered_output = balanced_list
                                    else:
                                        filtered_output = cleaned_section
                                else:
                                    filtered_output = cleaned_section
                        else:
                            filtered_output = cleaned_section
                else:
                    # Tenta lista JSON se não encontrou objeto
                    list_start = cleaned_section.find('[')
                    if list_start != -1:
                        balanced_list = _find_balanced_json(cleaned_section[list_start:], '[')
                        if balanced_list:
                            filtered_output = balanced_list
                        else:
                            filtered_output = cleaned_section
                    else:
                        filtered_output = cleaned_section
                
                filtered_output = filtered_output.strip()
                
                # Substitui vírgula por ponto em números (formato brasileiro)
                filtered_output = re.sub(r'(?<=\d),(?=\d)', '.', filtered_output)
            else:
                # Fallback: procura pelo último JSON válido no output (não o primeiro/exemplo)
                # Encontra todas as posições de '{' e tenta extrair JSON completo de cada uma
                json_candidates = []
                pos = 0
                while True:
                    pos = output.find('{', pos)
                    if pos == -1:
                        break
                    balanced_json = _find_balanced_json(output[pos:], '{')
                    if balanced_json:
                        json_candidates.append((pos, balanced_json))
                    pos += 1
                
                if json_candidates:
                    # Pega o último JSON encontrado (deve ser a resposta do modelo)
                    _, filtered_output = json_candidates[-1]
                    # Remove delimitadores markdown se houver
                    filtered_output = re.sub(r'^```json\s*', '', filtered_output, flags=re.MULTILINE)
                    filtered_output = re.sub(r'\s*```$', '', filtered_output, flags=re.MULTILINE)
                    filtered_output = filtered_output.strip()
                    # Substitui vírgula por ponto em números
                    filtered_output = re.sub(r'(?<=\d),(?=\d)', '.', filtered_output)
                else:
                    # Último recurso: retorna o output completo
                    filtered_output = output
            
            log(f"[infer] output filtrado (tamanho: {len(filtered_output)} chars, primeiros 500 chars): {filtered_output[:500]}")
            return filtered_output
        finally:
            # Remove arquivos temporários
            try:
                if os.path.exists(temp_img_path):
                    os.unlink(temp_img_path)
            except Exception:
                pass
            if temp_prompt_file and os.path.exists(temp_prompt_path):
                try:
                    os.unlink(temp_prompt_path)
                except Exception:
                    pass
            # Limpa cache e força garbage collection
            _clear_metal_cache()
            gc.collect()

    return await loop.run_in_executor(None, _run)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model": settings.model_id,
        "max_concurrency": settings.max_concurrency,
        "mlx_vlm_available": _HAS_MLX_VLM,
    }


@app.post("/extract/energy")
async def extract_energy(
    concessionaria: str = Form(...),
    uf: str = Form(...),
    file: UploadFile = File(...),
):
    t_request_start = time.time()
    log(f"[req] requisição recebida: concessionaria={concessionaria}, uf={uf}")
    
    if not _HAS_MLX_VLM:
        raise HTTPException(
            status_code=503,
            detail=(
                "Dependência 'mlx-vlm' não instalada/ativa (import mlx_vlm falhou). "
                "Ative o venv do projeto ou rode via `uv run ...`."
            ),
        )

    if not concessionaria.strip():
        raise HTTPException(status_code=400, detail="concessionaria é obrigatório")
    if not uf.strip():
        raise HTTPException(status_code=400, detail="uf é obrigatório")

    if file.content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(status_code=400, detail=f"content-type não suportado: {file.content_type}")

    raw = await file.read()
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"imagem acima do limite de {settings.max_image_mb}MB")

    t_start = time.time()
    log(f"[timing] início processamento: {(t_start - t_request_start)*1000:.1f}ms após receber requisição")
    
    img = None
    img_temp_path = None
    customer_crop_img = None
    consumption_crop_img = None
    customer_crop_path = None
    consumption_crop_path = None
    
    try:
        t_load_start = time.time()
        img = _load_image(raw)
        # Libera os bytes da imagem imediatamente após carregar
        del raw
        gc.collect()
        t_load_end = time.time()
        log(f"[timing] carregamento imagem: {(t_load_end - t_load_start)*1000:.1f}ms")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"falha ao abrir imagem: {e}")

    # Salva imagem temporariamente para detecção YOLO
    if _HAS_OBJECT_DETECTION and OBJECT_DETECTOR is not None:
        try:
            t_crop_start = time.time()
            img_temp_path = _save_image_temp(img)
            log(f"[crop] imagem salva temporariamente: {img_temp_path}")
            
            # Faz recorte de dados do cliente
            try:
                t_customer_start = time.time()
                customer_crop_path = OBJECT_DETECTOR.detect_and_crop_customer_data(img_temp_path)
                t_customer_end = time.time()
                log(f"[timing] detecção cliente: {(t_customer_end - t_customer_start)*1000:.1f}ms")
                if customer_crop_path:
                    customer_crop_img = Image.open(customer_crop_path).convert("RGB")
                    log(f"[crop] recorte cliente/endereço criado: {customer_crop_path}")
            except Exception as e:
                log(f"[crop] erro ao recortar cliente/endereço: {e}")
            
            # Faz recorte de consumo
            try:
                t_consumption_start = time.time()
                consumption_crop_path = OBJECT_DETECTOR.detect_and_crop_consumption(img_temp_path)
                t_consumption_end = time.time()
                log(f"[timing] detecção consumo: {(t_consumption_end - t_consumption_start)*1000:.1f}ms")
                if consumption_crop_path:
                    consumption_crop_img = Image.open(consumption_crop_path).convert("RGB")
                    log(f"[crop] recorte consumo criado: {consumption_crop_path}")
            except Exception as e:
                log(f"[crop] erro ao recortar consumo: {e}")
            
            t_crop_end = time.time()
            log(f"[timing] total recortes: {(t_crop_end - t_crop_start)*1000:.1f}ms")
        except Exception as e:
            log(f"[crop] erro ao processar recortes: {e}")

    t0 = time.time()
    log(f"[timing] tempo até início inferências: {(t0 - t_start)*1000:.1f}ms")
    
    # Prompt para imagem completa (dados gerais)
    prompt_full = _read_prompt(concessionaria, uf)
    prompt_full = f"""{prompt_full}

Contexto da requisição: UF={uf}, Concessionária={concessionaria}

Agora analise a imagem e retorne o JSON com os dados extraídos:"""
    
    log(f"[prompt] tamanho do prompt completo: {len(prompt_full)} caracteres")

    # Resultados das 3 inferências
    result_full = None
    result_customer = None
    result_consumption = None
    
    # Sem _GATE - cada subprocess é independente e pode rodar em paralelo
    # Inferência 1: Imagem completa (dados gerais)
    try:
        t_infer1_start = time.time()
        log("[infer] iniciando inferência imagem completa")
        result_full = await _infer_one(img, prompt_full)
        t_infer1_end = time.time()
        log(f"[timing] inferência completa: {(t_infer1_end - t_infer1_start)*1000:.1f}ms")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="timeout na inferência do modelo (imagem completa)")
    except Exception as e:
        log(f"[infer] erro na inferência imagem completa: {e}")
        result_full = None
    
    # Inferência 2: Recorte cliente/endereço
    if customer_crop_img is not None:
        try:
            t_infer2_start = time.time()
            log("[infer] iniciando inferência recorte cliente/endereço")
            prompt_customer = _read_customer_address_prompt(concessionaria, uf)
            result_customer = await _infer_one(customer_crop_img, prompt_customer)
            t_infer2_end = time.time()
            log(f"[timing] inferência cliente: {(t_infer2_end - t_infer2_start)*1000:.1f}ms")
        except Exception as e:
            log(f"[infer] erro na inferência cliente/endereço: {e}")
            result_customer = None
    else:
        result_customer = None
    
    # Inferência 3: Recorte consumo
    if consumption_crop_img is not None:
        try:
            t_infer3_start = time.time()
            log("[infer] iniciando inferência recorte consumo")
            prompt_consumption = _read_consumption_prompt()
            result_consumption = await _infer_one(consumption_crop_img, prompt_consumption)
            t_infer3_end = time.time()
            log(f"[timing] inferência consumo: {(t_infer3_end - t_infer3_start)*1000:.1f}ms")
        except Exception as e:
            log(f"[infer] erro na inferência consumo: {e}")
            result_consumption = None
    else:
        result_consumption = None
    
    # Limpa imagens da memória (fora do _GATE para não bloquear outras requisições)
    if img is not None:
        img.close()
        del img
    if customer_crop_img is not None:
        customer_crop_img.close()
        del customer_crop_img
    if consumption_crop_img is not None:
        consumption_crop_img.close()
        del consumption_crop_img
    
    # Remove arquivos temporários
    if img_temp_path and os.path.exists(img_temp_path):
        try:
            os.unlink(img_temp_path)
        except Exception:
            pass
    
    # Limpa arquivos temporários do ObjectDetection
    if _HAS_OBJECT_DETECTION and OBJECT_DETECTOR is not None:
        try:
            OBJECT_DETECTOR.cleanup_temp_files()
        except Exception:
            pass
    
    # Limpa cache do Metal e força garbage collection
    _clear_metal_cache()
    gc.collect()

    # Processa resultados e combina
    payload_full = {}
    payload_customer = {}
    payload_consumption = {}
    
    # Extrai JSON da inferência completa
    if result_full:
        try:
            payload_full = _extract_json(result_full)
            log(f"[infer] JSON imagem completa extraído: {json.dumps(payload_full, ensure_ascii=False)[:200]}")
        except Exception as e:
            log(f"[infer] ERRO ao extrair JSON imagem completa: {e}")
            log(f"[infer] resposta completa: {result_full[:500]}")
    
    # Extrai JSON do recorte cliente/endereço
    if result_customer:
        try:
            payload_customer = _extract_json(result_customer)
            log(f"[infer] JSON cliente/endereço extraído: {json.dumps(payload_customer, ensure_ascii=False)[:200]}")
        except Exception as e:
            log(f"[infer] ERRO ao extrair JSON cliente/endereço: {e}")
    
    # Extrai JSON do recorte consumo
    if result_consumption:
        try:
            payload_consumption = _extract_json(result_consumption)
            log(f"[infer] JSON consumo extraído: {json.dumps(payload_consumption, ensure_ascii=False)[:200]}")
        except Exception as e:
            log(f"[infer] ERRO ao extrair JSON consumo: {e}")
    
    # Combina resultados: dados gerais da imagem completa
    payload = payload_full.copy()
    
    # Sobrescreve com dados do endereço APENAS se o crop tem valor válido
    # O nome_cliente vem apenas da inferência principal, não do crop
    if payload_customer:
        for key in ["rua", "numero", "complemento", "bairro", "cidade", "estado", "cep"]:
            customer_value = payload_customer.get(key)
            # Só sobrescreve se o crop tem valor válido (não vazio)
            if customer_value and str(customer_value).strip():
                payload[key] = customer_value
    
    # Adiciona consumo_lista se disponível
    # IMPORTANTE: Não sobrescreve se payload_full já tem consumo_lista válido
    # Só adiciona/sobrescreve se o crop tiver dados melhores ou se payload_full não tiver
    if payload_consumption and "consumo_lista" in payload_consumption:
        consumo_crop = payload_consumption["consumo_lista"]
        consumo_full = payload.get("consumo_lista", [])
        
        # Só sobrescreve se:
        # 1. O crop tem lista não vazia E (payload_full não tem OU crop tem mais itens)
        # OU
        # 2. payload_full não tem consumo_lista ou está vazio
        if isinstance(consumo_crop, list) and len(consumo_crop) > 0:
            if not consumo_full or not isinstance(consumo_full, list) or len(consumo_full) == 0:
                # payload_full não tem dados, usa o crop
                payload["consumo_lista"] = consumo_crop
            elif len(consumo_crop) > len(consumo_full):
                # crop tem mais dados, usa o crop
                payload["consumo_lista"] = consumo_crop
            # Se ambos têm dados e crop não tem mais, mantém o payload_full
        elif not consumo_full or not isinstance(consumo_full, list) or len(consumo_full) == 0:
            # Se payload_full não tem dados, usa o crop mesmo que vazio
            payload["consumo_lista"] = consumo_crop
    
    payload = _ensure_contract(payload, concessionaria_input=concessionaria)

    ms = int((time.time() - t0) * 1000)
    log(f"[req] concessionaria={concessionaria.lower()} uf={uf.upper()} ms={ms}")
    _log_system_metrics("[req][mem]")

    return JSONResponse(content=payload)
