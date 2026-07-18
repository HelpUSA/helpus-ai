# AI HelpUS — Multi-AI cloud architecture

Updated: 2026-07-18
Status: foundation implemented
Scope: `HelpUSA/helpus-ai`

## Objective

AI HelpUS becomes an orchestrator of specialized models behind stable aliases.

## Aliases

- `helpus-fast`
- `helpus-general`
- `helpus-reasoner`
- `helpus-code`
- `helpus-vision`
- `helpus-verifier`
- `helpus-embedding`

## Components

- LiteLLM gateway;
- PostgreSQL;
- Redis;
- FastAPI router;
- cloud GPU endpoints;
- health checks and CI.

## Modes

- `single`: one specialist;
- `review`: primary model plus independent verifier and repair;
- `council`: multiple specialists, finalizer and optional verification.

## Security

Secrets stay outside Git. Services bind to localhost by default. Physical model
names remain hidden behind aliases. Models cannot invent tool or execution
receipts. `ai-bridge-local` remains external and unchanged.

## Next increment

MAI-2 provisions two live cloud endpoints, connects DeepSeek and a second open
model, then measures quality, latency, fallback and cost.

<!-- AI_HELPUS_MANAGED:RUNTIME_INTEGRATION_CONTINUATION_2026_07_18:START -->

## Ponte pendente entre fundação e runtime

Fluxo atual: `frontend -> POST /chat -> backend/main.py -> CerebroIA -> provedores legados`.

Fluxo alvo: `frontend -> POST /chat -> backend/main.py -> CerebroIA -> roteador multi-IA quando habilitado -> fallback legado quando necessário`.

Preservar a assinatura de `CerebroIA.pensar`.

Flags propostas: `HELPUS_MULTI_AI_ENABLED=false` e `HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=true`.

Detalhes: `docs/ai/HELPUS_RUNTIME_MULTI_AI_HANDOFF_2026-07-18.md`.

<!-- AI_HELPUS_MANAGED:RUNTIME_INTEGRATION_CONTINUATION_2026_07_18:END -->
