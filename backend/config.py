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
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
BUILD_COMMIT = os.getenv('BUILD_COMMIT', '')

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
ADMIN_EMAILS = [email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()]

# Multi-provider fallback
AI_PROVIDER_ORDER = [p.strip().lower() for p in os.getenv('AI_PROVIDER_ORDER', 'gemini,openrouter,deepseek').split(',') if p.strip()]
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/chat/completions')

# Optional HelpUS multi-AI runtime router.
# Disabled by default; legacy operation requires no new variable.
HELPUS_MULTI_AI_ENABLED = os.getenv(
    'HELPUS_MULTI_AI_ENABLED',
    'false',
).lower().strip() in ('1', 'true', 'yes', 'on')

HELPUS_MULTI_AI_BASE_URL = os.getenv(
    'HELPUS_MULTI_AI_BASE_URL',
    'http://127.0.0.1:8080',
).rstrip('/')

HELPUS_MULTI_AI_API_KEY = os.getenv(
    'HELPUS_MULTI_AI_API_KEY',
    '',
).strip()

try:
    HELPUS_MULTI_AI_TIMEOUT_SECONDS = float(
        os.getenv(
            'HELPUS_MULTI_AI_TIMEOUT_SECONDS',
            '180',
        )
    )
except (TypeError, ValueError):
    HELPUS_MULTI_AI_TIMEOUT_SECONDS = 180.0

if (
    HELPUS_MULTI_AI_TIMEOUT_SECONDS <= 0
    or HELPUS_MULTI_AI_TIMEOUT_SECONDS > 900
):
    HELPUS_MULTI_AI_TIMEOUT_SECONDS = 180.0

HELPUS_MULTI_AI_MODE = os.getenv(
    'HELPUS_MULTI_AI_MODE',
    'auto',
).lower().strip()

HELPUS_MULTI_AI_FALLBACK_TO_LEGACY = os.getenv(
    'HELPUS_MULTI_AI_FALLBACK_TO_LEGACY',
    'true',
).lower().strip() in ('1', 'true', 'yes', 'on')

HELPUS_MULTI_AI_DEFAULT_ALIAS = os.getenv(
    'HELPUS_MULTI_AI_DEFAULT_ALIAS',
    'helpus-general',
).lower().strip()
