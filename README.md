## extractor-energy

API FastAPI para extrair dados de faturas de energia com `mlx-vlm` (MLX, Apple Silicon).

### Rodar local (recomendado)

Use o ambiente do projeto (evita erro `ModuleNotFoundError: No module named 'mlx_vlm'` ao usar um Python global):

- `uv sync`
- `uv run uvicorn main:app --reload`

Alternativa (ativando venv):

- `source .venv/bin/activate`
- `uvicorn main:app --reload`

### Endpoints

- `GET /health`
- `POST /extract/energy` (form-data: `concessionaria`, `uf`, `file`)

### Prompts

Em `prompts/`:

- `base.md`: sempre aplicado
- `mapper.json`: mapeia `concessionaria` + `uf` -> arquivo `.md` (ex: `equatorial` + `go` -> `equatorial_go.md`)
- `mapper.json` também suporta `aliases` para padronizar entradas (ex: `cemig-d` -> `cemig`)
