# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

DATABASE_URL = os.getenv('DATABASE_URL')
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower().strip()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
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
GOOGLE_CLIENT_ID_DEFAULT = "812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com"
_raw_google_client_id = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_ID_CONFIGURED_EXPLICITLY = _raw_google_client_id is not None and bool(_raw_google_client_id.strip())
GOOGLE_CLIENT_ID = (_raw_google_client_id if GOOGLE_CLIENT_ID_CONFIGURED_EXPLICITLY else GOOGLE_CLIENT_ID_DEFAULT).strip()
ADMIN_EMAILS = [email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()]

# Multi-provider fallback
AI_PROVIDER_ORDER = [p.strip().lower() for p in os.getenv('AI_PROVIDER_ORDER', 'openai,gemini,openrouter,deepseek').split(',') if p.strip()]
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
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

# Concorrência e Isolamento Operacional (P0 - Ciclo 020)
# Enquanto o PostgreSQL de homologação estiver BLOCKED, a garantia de atomicidade
# e turn lock opera em memória local por processo. Em arquitetura multi-processos sem
# advisory lock distribuído (PostgreSQL pg_try_advisory_xact_lock), a operação DEVE ser
# restrita a 1 worker para garantir strictly-once sem janelas de concorrência.
MAX_OPERATIONAL_WORKERS = int(os.getenv("MAX_OPERATIONAL_WORKERS", "1"))
OPERATIONAL_CONCURRENCY_MODE = os.getenv("OPERATIONAL_CONCURRENCY_MODE", "single_worker_in_memory")


def validar_politica_seguranca_ambiente(enforce: bool = False) -> dict:
    """Avalia e opcionalmente bloqueia (fail-closed) a inicializacao por ambiente.

    Em staging e producao:
    - AUTH_REQUIRED deve ser estritamente True.
    - GOOGLE_CLIENT_ID deve ser configurado explicitamente via variavel de ambiente (sem fallback implicito).
    - Em staging, GOOGLE_CLIENT_ID nao pode reutilizar a credencial padrao de producao.
    - Se enforce=True e houver erros, lanca RuntimeError abortando o startup.
    Em desenvolvimento:
    - Tolera AUTH_REQUIRED=False e fallback para desenvolvimento local e suites automatizadas.
    """
    env = (ENVIRONMENT or "development").lower().strip()
    erros = []
    avisos = []
    client_id = (GOOGLE_CLIENT_ID or "").strip()
    prod_default_client_id = "812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com"

    # Determina se GOOGLE_CLIENT_ID foi explicitamente configurado pelo ambiente
    raw_env_client_id = os.getenv("GOOGLE_CLIENT_ID")
    env_has_explicit = raw_env_client_id is not None and bool(raw_env_client_id.strip())
    is_explicit = (
        env_has_explicit
        or bool(globals().get("GOOGLE_CLIENT_ID_CONFIGURED_EXPLICITLY", False))
        or (bool(client_id) and client_id != prod_default_client_id)
    )

    if env in ("production", "staging"):
        if not AUTH_REQUIRED:
            erros.append("AUTH_REQUIRED deve ser estritamente True em ambiente protegido (staging/production).")

        if not client_id:
            erros.append("GOOGLE_CLIENT_ID ausente. O ambiente protegido exige configuracao explicita de Client ID.")
        elif env == "staging" and client_id == prod_default_client_id:
            erros.append("GOOGLE_CLIENT_ID em staging nao pode reutilizar a credencial padrao de producao. Exigir Client ID dedicado.")
        elif not is_explicit:
            erros.append(
                f"GOOGLE_CLIENT_ID nao foi configurado explicitamente via variavel de ambiente em {env}. "
                "O uso de fallback implicito/hardcoded e terminantemente proibido em staging e producao."
            )

        if not ADMIN_EMAILS:
            avisos.append("ADMIN_EMAILS vazio. Endpoints /admin/* operarao em fail-closed total (403).")

    if enforce and erros:
        raise RuntimeError(f"Bloqueio de seguranca fail-closed no startup ({env}): {'; '.join(erros)}")

    return {
        "environment": env,
        "auth_required": bool(AUTH_REQUIRED),
        "google_client_id_configured": bool(client_id),
        "google_client_id_explicit": bool(is_explicit),
        "admin_emails_count": len(ADMIN_EMAILS),
        "conforme": len(erros) == 0,
        "erros": erros,
        "avisos": avisos,
    }
