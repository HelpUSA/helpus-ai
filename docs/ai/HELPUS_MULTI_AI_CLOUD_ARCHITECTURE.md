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
