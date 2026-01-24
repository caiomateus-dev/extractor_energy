## extractor-energy

API FastAPI para extrair dados de faturas de energia com `mlx-vlm` (MLX, Apple Silicon).

### Estrutura

```
extractor_energy/
├── main.py           # App FastAPI, inclui router
├── config.py         # Settings
├── core/             # Utilitários: prompts, imagens, JSON, normalização, adapters
├── inference/        # Bootstrap do modelo, inferência VLM
├── api/              # Rotas: /health, /extract/energy
├── detectors/        # YOLO para recortes (cliente, consumo)
├── prompts/          # base.md, mapper.json, specs por concessionária
├── adapters/         # LoRA por concessionária_UF
├── utils/
└── training/
```

### Rodar local

- `uv sync`
- `uv run uvicorn main:app --reload`

**Requisições em paralelo:** Metal (Apple Silicon) não é thread-safe. Em um mesmo processo só roda 1 inferência por vez. Para 2+ requisições em paralelo, use vários workers (cada worker = 1 processo = 1 Metal):

- `uv run uvicorn main:app --workers 2`

### Endpoints

- `GET /health`
- `POST /extract/energy` (form-data: `concessionaria`, `uf`, `file`)

### Prompts

Em `prompts/`:

- `base.md`: sempre aplicado
- `mapper.json`: mapeia `concessionaria` + `uf` -> arquivo `.md`
- `mapper.json` suporta `aliases` (ex: `cemig-d` -> `cemig`)
