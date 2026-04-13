"""FastAPI application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure `src` is on sys.path when running `uvicorn api.main:app` from repo root.
_SRC_ROOT = Path(__file__).resolve().parents[1]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from utils.logging_utils import configure_logging

configure_logging()

app = FastAPI(title="AI Learning Path Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
