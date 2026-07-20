# Implantação Multi-IA no Railway

Atualizado em: 2026-07-20

## Multi-AI Router

- repositório: `HelpUSA/helpus-ai`;
- branch: `main`;
- Dockerfile: `services/multi_ai_router/Dockerfile`;
- porta: `8080`;
- healthcheck: `/healthz`.

## LiteLLM

- porta: `4000`;
- configuração: `infra/multi-ai/litellm-config.yaml`;
- secrets somente no Railway.

## Backend inicialmente

- `HELPUS_MULTI_AI_ENABLED=false`;
- `HELPUS_MULTI_AI_BASE_URL=http://multi-ai-router.railway.internal:8080`;
- `HELPUS_MULTI_AI_TIMEOUT_SECONDS=180`;
- `HELPUS_MULTI_AI_MODE=auto`;
- `HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=true`;
- `HELPUS_MULTI_AI_DEFAULT_ALIAS=helpus-general`.

## Sequência

Auditar infraestrutura, criar staging, implantar LiteLLM, implantar roteador, configurar rede privada e secrets, testar aliases, modos e fallback e ativar gradualmente.
