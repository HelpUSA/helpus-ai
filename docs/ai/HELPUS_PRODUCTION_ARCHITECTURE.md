# Arquitetura de Produção HelpUS

Atualizado em: 2026-07-20

## Fluxo oficial

Usuário → Frontend Vercel → Backend Railway → Multi-AI Router → LiteLLM → Providers.

Serviços auxiliares no Railway: PostgreSQL e Redis, quando necessários.

## Públicos

- frontend;
- backend.

## Privados

- Multi-AI Router;
- LiteLLM;
- PostgreSQL;
- Redis.

## Rede privada

Backend para roteador:

`http://multi-ai-router.railway.internal:8080`

Roteador para LiteLLM:

`http://litellm.railway.internal:4000/v1`

## Segurança

Nenhum segredo no Git ou frontend. Roteador e LiteLLM privados, autenticação interna, logs sanitizados, rate limits e limites financeiros.

## Computador local

Somente desenvolvimento, testes, diagnóstico e manutenção.
