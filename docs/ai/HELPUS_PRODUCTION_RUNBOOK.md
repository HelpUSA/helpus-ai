# Runbook de Produção Multi-IA

Atualizado em: 2026-07-20

## Saúde

Validar:

- `/healthz`;
- `/readyz`;
- `/v1/models`.

## Ativação

Começar com `helpus-general`, modo `single` e fallback ligado.

Depois liberar:

- `auto`;
- demais aliases;
- `review`;
- por último, `council`.

## Rollback

Definir:

`HELPUS_MULTI_AI_ENABLED=false`

## Monitoramento

Acompanhar request ID, alias, modo, provider, modelo, latência, tokens, fallback e categoria de erro.

Nunca registrar secrets ou headers de autorização.
