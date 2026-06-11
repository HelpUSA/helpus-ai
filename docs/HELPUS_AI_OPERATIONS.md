# HelpUS AI - Documento principal de operacao

Data-base: 2026-06-11

Este e o documento principal de estado operacional e validacao do HelpUS AI. Os demais arquivos em docs ficam como historico, planejamento ou detalhe auxiliar.

## Estado atual

- Producao ativa no frontend Vercel: https://ai.helpusbr.com.
- Backend ativo no Railway: https://helpus-api-production.up.railway.app.
- Banco de dados: Postgres no Railway.
- Autenticacao: AUTH_REQUIRED=true.
- Login Google obrigatorio para uso normal do chat.
- Admin dashboard ativo em /admin e protegido por conta Google admin.
- Endpoint publico de status ativo em /status.
- Provider principal: DeepSeek.
- Fallback configurado: Gemini e OpenRouter.
- O backend ja retorna provider_used e fallback_reason nas respostas de chat.
- O frontend oculta o badge de provider por padrao e aparece apenas em modo debug.
- Conversas persistem por session_id.
- Projetos sao suportados no frontend por project_id.

## Provider e fallback

Objetivo operacional atual:

1. Usar DeepSeek como provider principal.
2. Manter Gemini e OpenRouter como fallback.
3. Expor observabilidade suficiente para confirmar:
   - provider configurado;
   - provider usado;
   - motivo de fallback;
   - modelo;
   - latencia.

Campos relevantes:

- provider_configured
- provider_used
- fallback_reason
- model
- latency_ms

## Endpoint interno smoke-chat

Ha um patch local pendente de revisao, ainda sem commit e sem deploy, adicionando:

- rota: POST /internal/smoke-chat
- header: x-internal-smoke-token
- env esperada: INTERNAL_SMOKE_TOKEN
- comportamento esperado: HTTP 401 se env ausente, token ausente ou token invalido
- resposta esperada: ok, resposta, provider_configured, provider_used, fallback_reason, model e latency_ms

Antes de usar em producao, configurar INTERNAL_SMOKE_TOKEN no Railway e validar o endpoint com token real. O token nao deve ser logado nem exposto no frontend.

## Admin dashboard

O admin dashboard deve exibir ou consumir metricas de provider retornadas pelo backend:

- provider configurado;
- provider usado;
- fallback_reason;
- modelo;
- latencia.

Status atual: o backend local no patch pendente passa a retornar metricas de provider em /status e /admin/status. A UI mais visual do admin pode receber melhoria especifica se necessario.

## Runbook de validacao

Antes de commit:

```bash
git status -sb
python -m py_compile backend/config.py backend/banco.py backend/cerebro.py backend/buscador.py backend/auth.py backend/main.py
npm --prefix frontend run build
git diff --check
npm run smoke:prod
git diff --stat
```

Antes de deploy:

```bash
git log --oneline -10
railway status
npm run smoke:prod
```

Depois de deploy:

```bash
npm run smoke:prod
```

Conferir manualmente:

- https://ai.helpusbr.com
- https://ai.helpusbr.com/admin
- https://helpus-api-production.up.railway.app/status

## Smoke de producao

Arquivo:

```text
scripts/29_smoke_prod.js
```

Comando:

```bash
npm run smoke:prod
```

Saida esperada:

```text
OK saude
OK status
OK front
OK admin
HELPUS_SMOKE_OK
```

## Regras de mudanca

- Aplicar sempre o menor patch possivel.
- Reportar git diff --stat e resumo do diff antes de commit.
- Nao commitar sem validacoes.
- Nao fazer deploy sem aprovacao explicita.
- Nunca adicionar chaves reais ao repositorio.
- Nao expor tokens em logs, frontend ou docs publicas.
- Smoke interno deve evitar PII e dados sensiveis.

## Proximas atividades

1. Revisar o patch local do endpoint interno POST /internal/smoke-chat.
2. Configurar INTERNAL_SMOKE_TOKEN no Railway somente quando o patch for aprovado para deploy.
3. Criar ou atualizar smoke automatizado para validar o endpoint interno com token.
4. Confirmar em producao que provider_used=deepseek quando DeepSeek responder corretamente.
5. Melhorar a visualizacao das metricas de provider no admin, se necessario.
6. Registrar metricas agregadas de uso por provider sem PII.
7. Revisar documentos antigos em docs e arquivar apenas depois de aprovacao explicita.

## Documentos auxiliares

- HELPUS_AI_OVERVIEW.md: visao geral historica.
- HELPUS_AI_ROADMAP.md: roadmap.
- AI_PROVIDER_FALLBACK.md: detalhes do fallback.
- HELPUS_AI_FALLBACK_STATUS_2026-06-08.md: status historico datado.
- PRODUCTION_CHECKLIST.md: checklist historico de producao.
- MULTI_AI_PROVIDER_PLAN.md: plano antigo/resumido de multi-provider.

Documento antigo ou redundante identificado: MULTI_AI_PROVIDER_PLAN.md. Ele e curto e coberto por AI_PROVIDER_FALLBACK.md e por este documento principal. Nao foi removido neste patch para evitar perda de historico sem aprovacao explicita.
