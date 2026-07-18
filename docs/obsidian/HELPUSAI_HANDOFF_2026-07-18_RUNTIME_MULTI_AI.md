# HelpUSAI — Handoff runtime multi-IA — 2026-07-18

## Estado atual

- Baseline: `bb654664597aba79d7c33bc87afe54c3e25243b1`
- Branch: `main`
- Fundação LiteLLM e roteador: concluída
- Aliases: 7
- Modos: `single`, `review`, `council`
- Integração com `/chat`: pendente
- GPU: não provisionada
- Credenciais: não adicionadas
- AI Bridge Local: não modificado

## Documento principal

`docs/ai/HELPUS_RUNTIME_MULTI_AI_HANDOFF_2026-07-18.md`

## Arquivos críticos

- `backend/config.py`
- `backend/cerebro.py`
- `backend/main.py`
- `backend/helpus_memory_reader.py`
- `backend/helpus_internal_memory_recorder.py`
- `services/multi_ai_router/app.py`
- `services/multi_ai_router/router_core.py`
- `scripts/32_test_fallback_order.py`

## Contrato

`POST /chat` chama `CerebroIA.pensar` e retorna texto, tokens e latência.

Fallback: `gemini,openrouter,deepseek`.

## Próxima atividade

Criar integração backend opcional, desligada por padrão, com cliente multi-IA, variáveis `HELPUS_MULTI_AI_*`, integração em `CerebroIA`, fallback legado, mocks, regressão, documentação, commit e push.

## Não repetir

- não recriar a fundação;
- não remover `.env.example`;
- não alterar Watcher;
- não alterar `ai-bridge-local`;
- não incluir credenciais;
- não remover fallback;
- não criar executor de comandos.

## Encerramento esperado

Flag desligada preserva legado; flag ligada usa roteador; falha retorna ao legado; prompt e memória preservados; testes aprovados; push concluído; repositório limpo e sincronizado.
