# OCR-Anchored Pipeline

Pipeline alternativo para extração de dados de faturas de energia usando detecção de âncoras via OCR e inferências VLM focadas em crops pequenos.

## Arquitetura

### Componentes

1. **`ocr_detector.py`**: Detecção de texto usando PaddleOCR
   - Detecta bounding boxes de texto na imagem completa
   - Retorna texto reconhecido com coordenadas

2. **`anchor_detector.py`**: Detecção de âncoras (palavras-chave)
   - Busca palavras-chave relacionadas a cada campo (ex: "VENCIMENTO", "ICMS")
   - Usa regex para matching flexível
   - Seleciona a melhor âncora baseada em score e posição

3. **`crop_generator.py`**: Geração de crops ao redor das âncoras
   - Gera crops pequenos com contexto ao redor de cada âncora
   - Configurável: padding, tamanho mínimo/máximo

4. **`field_extractors.py`**: Prompts curtos por campo
   - Prompts específicos e focados para cada campo
   - Reduz tokens de geração e melhora velocidade

5. **`tiling_fallback.py`**: Fallback com tiling
   - Divide imagem em tiles quando âncoras não são encontradas
   - Garante cobertura mesmo em casos extremos

6. **`vlm_inference.py`**: Inferência VLM em crops pequenos
   - Chama MLX-VLM apenas nos crops gerados
   - Timeout reduzido e max_tokens baixo

## Fluxo de Processamento

```
1. OCR na imagem completa → detecta textos e bboxes
2. Busca âncoras para cada campo → encontra palavras-chave
3. Gera crops ao redor das âncoras → cria imagens pequenas
4. VLM em cada crop → extrai campo específico
5. Fallback tiling → se algum campo não foi encontrado
6. YOLO para endereço/consumo → mantém lógica existente
7. Inferência full-image → para campos restantes
```

## Vantagens

- **Velocidade**: Múltiplas inferências pequenas são mais rápidas que 1 inferência grande
- **Precisão**: Prompts focados reduzem alucinações
- **Resiliência**: Funciona mesmo com variações de layout
- **Eficiência**: Menos pixels processados = menos memória

## Uso

```python
# Rodar o servidor
uvicorn main_ocr_anchored:app --host 0.0.0.0 --port 8001

# Endpoint
POST /extract/energy
Form data:
  - concessionaria: str
  - uf: str
  - file: image file
```

## Dependências

- `paddleocr>=2.7.0`: Para detecção de texto
- `mlx-vlm`: Para inferência VLM
- `pillow`: Para processamento de imagens
- `ultralytics`: Para YOLO (endereço/consumo)

## Configuração

Os parâmetros podem ser ajustados em cada módulo:

- `CropGenerator`: `padding_x`, `padding_y`, tamanhos min/max
- `AnchorDetector`: Padrões de regex para cada campo
- `TilingFallback`: Tamanho de tiles, overlap
- `FieldExtractorPrompts`: Prompts por campo
