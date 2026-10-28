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


PROD_ENV_ALIASES = {"production", "prod"}
STAGING_ENV_ALIASES = {"staging", "stage"}
DEV_ENV_ALIASES = {"development", "dev", "test", "testing", "local"}
PROTECTED_ENVIRONMENTS = PROD_ENV_ALIASES | STAGING_ENV_ALIASES
VALID_ENVIRONMENTS = PROTECTED_ENVIRONMENTS | DEV_ENV_ALIASES

DEPLOY_INDICATOR_VARS = (
    "VERCEL",
    "VERCEL_ENV",
    "VERCEL_URL",
    "RAILWAY_ENVIRONMENT",
    "RAILWAY_PROJECT_ID",
    "RENDER",
    "RENDER_SERVICE_ID",
    "FLY_ALLOC_ID",
    "FLY_APP_NAME",
    "AWS_EXECUTION_ENV",
    "AWS_LAMBDA_FUNCTION_NAME",
    "KUBERNETES_SERVICE_HOST",
    "HEROKU_APP_ID",
    "DIGITALOCEAN_APP_ID",
    "NETLIFY",
    "DENO_DEPLOYMENT_ID",
    "GOOGLE_CLOUD_PROJECT",
    "GAE_APPLICATION",
    "K_SERVICE",
)


def validar_politica_seguranca_ambiente(enforce: bool = False, env_source: Optional[dict] = None) -> dict:
    """Avalia e opcionalmente bloqueia (fail-closed) a inicializacao por ambiente.

    Fonte Unica de Verdade e Deploy Environment Gate (Ordem 089):
    - Em qualquer contexto de deploy cloud (Vercel, Railway, Render, Fly, Lambda, K8s, etc.):
      * ENVIRONMENT ausente ou vazio e expressamente proibido (sem fallback silencioso para dev).
      * Ambientes de desenvolvimento ('development', 'dev', 'local', 'test') sao terminantemente proibidos.
      * Exige declaracao explicita de ambiente protegido homologado (staging, stage, prod, production).
      * Invariantes de autenticacao sao compulsoriamente impostas (is_protected=True).
    - O GOOGLE_CLIENT_ID deve provir comprovadamente do ambiente (variavel no SO ou env_source).
    - Alteracoes exclusivas em memoria (sem variavel de ambiente) sao rejeitadas em ambientes protegidos.
    - Se enforce=True e houver erros, lanca RuntimeError abortando o startup.
    - Em desenvolvimento local offline sem deploy vars: tolera fallback e AUTH_REQUIRED=False.
    """
    lookup = env_source if env_source is not None else os.environ
    prod_default_client_id = "812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com"
    erros = []
    avisos = []

    # Deteccao rigorosa de contexto de deploy cloud (inclusive variavel presente mas vazia)
    in_deploy = any(var_name in lookup for var_name in DEPLOY_INDICATOR_VARS)

    # Resolucao de ENVIRONMENT a partir do lookup ou modulo
    raw_env_lookup = lookup.get("ENVIRONMENT")
    env_from_module = globals().get("ENVIRONMENT")
    if isinstance(env_from_module, str):
        env_from_module = env_from_module.strip()
    else:
        env_from_module = ""

    if in_deploy:
        # Contexto de Deploy: proibido defaulting silencioso para development
        if raw_env_lookup is None or not str(raw_env_lookup).strip():
            raw_env_name = env_from_module if env_from_module and env_from_module.lower().strip() in PROTECTED_ENVIRONMENTS else ""
            if not raw_env_name:
                erros.append(
                    "ENVIRONMENT ausente ou vazio em contexto de deploy cloud. "
                    "Deploy exige declaracao explicita de ambiente protegido homologado (production, prod, staging, stage)."
                )
                raw_env_name = "unspecified_deploy"
        else:
            raw_env_name = str(raw_env_lookup).strip()

        env = raw_env_name.lower().strip()

        if env in DEV_ENV_ALIASES:
            erros.append(
                f"Ambiente de desenvolvimento '{raw_env_name}' e terminantemente proibido em contexto de deploy cloud. "
                "Deploy requer ambiente protegido homologado (production, prod, staging, stage)."
            )
        elif env not in PROTECTED_ENVIRONMENTS and env != "unspecified_deploy":
            erros.append(
                f"Ambiente nao homologado '{raw_env_name}' em contexto de deploy cloud. "
                "Deploy requer ambiente protegido valido (production, prod, staging, stage)."
            )

        # Em deploy cloud, o modo e forcadamente protegido para avaliar todas as salvaguardas
        is_protected = True
        is_prod = env in PROD_ENV_ALIASES
        is_staging = env in STAGING_ENV_ALIASES
    else:
        # Modo Local: desenvolvimento desimpedido fora de cloud
        if env_source is not None and "ENVIRONMENT" in env_source:
            raw_env_name = env_source["ENVIRONMENT"]
        elif env_from_module and env_from_module.lower().strip() in PROTECTED_ENVIRONMENTS:
            raw_env_name = env_from_module
        elif raw_env_lookup and raw_env_lookup.lower().strip() in PROTECTED_ENVIRONMENTS:
            raw_env_name = raw_env_lookup
        else:
            raw_env_name = raw_env_lookup or env_from_module or "development"

        env = raw_env_name.lower().strip()
        is_prod = env in PROD_ENV_ALIASES
        is_staging = env in STAGING_ENV_ALIASES
        is_protected = is_prod or is_staging

    # Resolucao de AUTH_REQUIRED (suporta lookup ou modulo)
    auth_from_lookup = lookup.get("AUTH_REQUIRED")
    if auth_from_lookup is not None:
        auth_required = str(auth_from_lookup).lower().strip() in ("1", "true", "yes", "on")
    else:
        auth_required = bool(globals().get("AUTH_REQUIRED"))

    # Resolucao de ADMIN_EMAILS
    if "ADMIN_EMAILS" in lookup:
        admin_emails = [email.strip().lower() for email in lookup.get("ADMIN_EMAILS", "").split(",") if email.strip()]
    else:
        admin_emails = list(globals().get("ADMIN_EMAILS") or [])

    # Fonte unica de verdade para GOOGLE_CLIENT_ID: exclusivamente a variavel de ambiente
    raw_env_client_id = lookup.get("GOOGLE_CLIENT_ID")
    is_explicit = raw_env_client_id is not None and bool(raw_env_client_id.strip())
    client_id = (raw_env_client_id if is_explicit else (globals().get("GOOGLE_CLIENT_ID") or "")).strip()

    if is_protected:
        if not auth_required:
            erros.append(f"AUTH_REQUIRED deve ser estritamente True em ambiente protegido ({env}).")

        if not client_id:
            erros.append(f"GOOGLE_CLIENT_ID ausente ou vazio. O ambiente protegido ({env}) exige configuracao explicita de Client ID.")
        elif is_staging and client_id == prod_default_client_id:
            erros.append("GOOGLE_CLIENT_ID em staging nao pode reutilizar a credencial padrao de producao. Exigir Client ID dedicado.")
        elif not is_explicit:
            erros.append(
                f"GOOGLE_CLIENT_ID nao foi configurado explicitamente via variavel de ambiente em {env}. "
                "O uso de fallback de codigo ou alteracao exclusiva em memoria e terminantemente proibido."
            )

        if not admin_emails:
            avisos.append("ADMIN_EMAILS vazio. Endpoints /admin/* operarao em fail-closed total (403).")

    if enforce and erros:
        raise RuntimeError(f"Bloqueio de seguranca fail-closed no startup ({env}): {'; '.join(erros)}")

    return {
        "environment": env,
        "is_protected": is_protected,
        "is_deploy_context": in_deploy,
        "auth_required": bool(auth_required),
        "google_client_id_configured": bool(client_id),
        "google_client_id_explicit": bool(is_explicit),
        "admin_emails_count": len(admin_emails),
        "conforme": len(erros) == 0,
        "erros": erros,
        "avisos": avisos,
    }
