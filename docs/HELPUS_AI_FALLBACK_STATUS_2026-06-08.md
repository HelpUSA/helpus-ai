# HelpUS AI fallback status - 2026-06-08

## Status atual

Fallback multi-provider implementado e publicado no backend. Ordem efetiva: Gemini -> OpenRouter -> DeepSeek.

Default atual: AI_PROVIDER_ORDER=gemini,openrouter,deepseek.

## Commits publicados

- a32e4d4 OpenRouter-fallback-for-Gemini
- 79e7288 Add-DeepSeek-fallback-after-OpenRouter
- 3436917 Add-DeepSeek-to-default-provider-order
- ac924a8 Add-provider-config-smoke
- eeecf0f Add-provider-key-guards
- 96b955c Add-AI-provider-fallback-doc

## Validacoes executadas

- python -m py_compile backend/config.py backend/cerebro.py backend/main.py scripts/30_smoke_ai_providers.py
- npm run smoke:providers
- npm run smoke:prod
- git diff --check

## Smokes

Publicado: scripts/30_smoke_ai_providers.py via npm run smoke:providers.

Publicado: scripts/31_smoke_prod_chat.js via npm run smoke:chat. Sem HELPUS_GOOGLE_ID_TOKEN ele imprime CHAT_SMOKE_SKIPPED_AUTH_REQUIRED e sai 0. Com token valido, executa POST /chat e valida resposta/session_id.

## Teste real do chat

POST anonimo para https://helpus-api-production.up.railway.app/chat retornou HTTP 401. Isso e esperado porque producao exige Authorization: Bearer <Google ID token>. Nao e indicio de falha do fallback.

## Guards de chave

- OPENROUTER_API_KEY ausente: fallback segue para DeepSeek.
- DEEPSEEK_API_KEY ausente: falha explicita sem chamada invalida.

## Proximas atividades

1. smoke:chat publicado no package.json e validado sem token em 2026-06-10.
2. Rodar smoke:chat com HELPUS_GOOGLE_ID_TOKEN valido quando houver token operacional.
3. provider_used e fallback_reason adicionados ao contrato de resposta /chat em 2026-06-10; fallback_reason detalhado por fallback real ainda pendente.
4. Refatorar fallback para loop baseado em AI_PROVIDER_ORDER.
5. Encoding de backend/main.py, backend/cerebro.py e backend/config.py verificado em 2026-06-10 sem caracteres quebrados.
6. Atualizar PRODUCTION_CHECKLIST.md com itens de providers.
7. Adicionar versao/commit no /status ou /admin.
8. Criar testes unitarios de fallback com mocks.

## Status endpoint metadata - 2026-06-08

Commit 680745a adds safe metadata to /status: app_version, build_commit, auth_required, and provider_order. These fields help verify deployed version and provider configuration without exposing API keys, bearer tokens, prompts, or full provider responses. Production may briefly show the old /status shape until deploy propagation completes.
