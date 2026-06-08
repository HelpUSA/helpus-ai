# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/assistente')
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower().strip()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openrouter/auto')
AI_REVIEW_ENABLED = os.getenv('AI_REVIEW_ENABLED', 'false').lower().strip() in ('1', 'true', 'yes', 'on')
AI_REVIEW_PROVIDER = os.getenv('AI_REVIEW_PROVIDER', 'openrouter').lower().strip()
AI_REVIEW_TIMEOUT = float(os.getenv('AI_REVIEW_TIMEOUT', '12'))
MODEL_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'modelos' / 'qwen2.5-3b-instruct-q4_k_m.gguf'))

MODEL_CONFIG = {
    'n_ctx': int(os.getenv('MODEL_N_CTX', '4096')),
    'n_threads': int(os.getenv('MODEL_N_THREADS', '4')),
    'n_batch': int(os.getenv('MODEL_N_BATCH', '256')),
    'max_tokens': int(os.getenv('MODEL_MAX_TOKENS', '800')),
    'temperature': float(os.getenv('MODEL_TEMPERATURE', '0.7')),
}

SEARCH_CONFIG = {'user_agent': 'HelpUS/1.0', 'timeout': 15.0, 'max_results': 5}
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = ENVIRONMENT == 'development'


CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://ai.helpusbr.com,https://helpus-ai.vercel.app,http://localhost:3000"
    ).split(",")
    if origin.strip()
]


AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower().strip() in ("1", "true", "yes", "on")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Multi-provider fallback
AI_PROVIDER_ORDER = [p.strip().lower() for p in os.getenv('AI_PROVIDER_ORDER', 'gemini,openrouter').split(',') if p.strip()]
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/chat/completions')
