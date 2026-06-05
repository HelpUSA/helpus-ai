# -*- coding: utf-8 -*-
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/assistente"
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    str(BASE_DIR / "modelos" / "tinyllama.gguf")
)

MODEL_CONFIG = {
    "n_ctx": 4096,
    "n_threads": 8,
    "n_batch": 256,
    "max_tokens": 800,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1
}

SEARCH_CONFIG = {
    "user_agent": "HelpUS/1.0",
    "timeout": 15.0,
    "max_results": 5
}

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"