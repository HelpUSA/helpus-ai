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

## Atividade concluída em 2026-07-20

A integração backend opcional foi implementada, desligada por padrão, com cliente multi-IA, variáveis `HELPUS_MULTI_AI_*`, integração em `CerebroIA`, fallback legado, mocks, regressão e documentação.

O commit e o push foram concluídos. A etapa atual é a implantação cloud.

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

<!-- AI_HELPUS_MANAGED:RUNTIME_MULTI_AI_HANDOFF_UPDATE_20260720 -->

## Evidências da integração

- documento técnico: `../ai/HELPUS_RUNTIME_MULTI_AI_INTEGRATION.md`;
- teste: `tests/test_multi_ai_runtime_integration.py`;
- validador: `scripts/83_validate_multi_ai_runtime.py`;
- comandos npm: `test:multi-ai-runtime`, `smoke:multi-ai-runtime` e `test:multi-ai-integration`;
- aliases: `helpus-fast`, `helpus-general`, `helpus-reasoner`, `helpus-code`, `helpus-vision`, `helpus-verifier` e `helpus-embedding`;
- GPU: não provisionada;
- credenciais: não adicionadas;
- AI Bridge Local: não alterado.

<!-- HELPUS_OBSIDIAN_CLOUD_STATUS_START -->

## Atualização cloud

O runtime multi-IA foi concluído e publicado.

Commit:

`cb917bec48a73d44dfceb2c038738cd429a32134`

A frente atual é a implantação no Railway.

<!-- HELPUS_OBSIDIAN_CLOUD_STATUS_END -->
