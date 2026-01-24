"""
Energy Extractor – MLX-VLM + Qwen2.5-VL.

Uso: `uv run uvicorn main:app --reload`
Com vários workers: `uv run uvicorn main:app --workers 3`
"""

from fastapi import FastAPI

from api.routes import router

app = FastAPI(title="Energy Extractor (MLX-VLM + Qwen2.5-VL)")
app.include_router(router)
