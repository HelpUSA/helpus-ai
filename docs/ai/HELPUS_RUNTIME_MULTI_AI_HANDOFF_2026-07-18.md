# AI HelpUS — Handoff de continuidade da integração runtime multi-IA

Data: 18 de julho de 2026.

Este documento é o ponto de entrada obrigatório para qualquer novo chat ou agente que continue o desenvolvimento da aplicação AI HelpUS.

## 1. Repositório e baseline

- Repositório local: `D:\dev\ai`
- Remoto: `HelpUSA/helpus-ai`
- Branch: `main`
- Upstream: `origin/main`
- Baseline da fundação: `bb654664597aba79d7c33bc87afe54c3e25243b1`
- Commit: `feat(ai): add multi-model cloud gateway foundation`
- Estado confirmado: limpo, sincronizado e `HEAD == origin/main`.

Antes de qualquer escrita, executar `git fetch` e validar branch, upstream, HEAD, origin/main, stage, worktree, arquivos não rastreados e divergência.

## 2. Objetivo do AI HelpUS

O AI HelpUS deve permanecer uma aplicação da HelpUS, em português do Brasil, com identidade própria, memória, busca, fallback entre provedores, rastreabilidade operacional e integração segura com Watcher e AI Bridge Local.

O assistente não deve se apresentar como Gemini, OpenAI, ChatGPT, DeepSeek ou qualquer modelo físico. A identidade pública é HelpUS.

Nunca inventar recibos `[AI_LOCAL]` ou `[AI_LOCAL_RUN]`, IDs, `command_id`, caminhos, resultados, envelopes incompletos, commits, pushes ou deploys.

## 3. Fundação multi-IA concluída

O commit `bb654664597aba79d7c33bc87afe54c3e25243b1` criou:

- LiteLLM;
- PostgreSQL e Redis;
- roteador FastAPI;
- Docker Compose;
- aliases estáveis;
- modos `single`, `review` e `council`;
- fallback entre aliases;
- testes unitários;
- CI;
- documentação técnica.

Aliases:

- `helpus-fast`
- `helpus-general`
- `helpus-reasoner`
- `helpus-code`
- `helpus-vision`
- `helpus-verifier`
- `helpus-embedding`

Arquivos principais:

- `infra/multi-ai/docker-compose.yml`
- `infra/multi-ai/litellm-config.yaml`
- `infra/multi-ai/.env.example`
- `services/multi_ai_router/app.py`
- `services/multi_ai_router/router_core.py`
- `services/multi_ai_router/Dockerfile`
- `tests/test_multi_ai_router_core.py`
- `scripts/82_validate_multi_ai_foundation.py`
- `.github/workflows/multi-ai-foundation.yml`

Resultado validado:

- 17 arquivos no escopo exato;
- 512 linhas adicionadas;
- 6 testes aprovados;
- `MODEL_ALIAS_COUNT=7`;
- commit e push concluídos;
- repositório limpo e sincronizado.

## 4. Incidente de `.env.example`

`infra/multi-ai/.env.example` estava oculto por regra preexistente de ignore. A primeira execução encontrou 16 arquivos em vez de 17, não criou commit, não fez push e executou rollback limpo.

Correção aplicada:

```powershell
git add -f -- infra/multi-ai/.env.example
```

O arquivo contém somente placeholders. Nenhuma credencial foi versionada. Não remover ou renomear sem atualizar Compose, documentação, testes e CI.

## 5. Pendências

A fundação existe, mas o runtime ainda não chama o roteador multi-IA.

Pendentes:

- conta de provedor;
- GPU;
- endpoint vLLM;
- modelos físicos;
- região e hardware;
- credenciais reais;
- `.env` local de produção;
- deploy em servidor;
- mudança de tráfego.

Marcadores:

- `CLOUD_GPU_PROVISIONED=False`
- `PROVIDER_CREDENTIALS_ADDED=False`
- `AI_BRIDGE_LOCAL_MODIFIED=False`

## 6. Runtime real

### 6.1 Endpoint

Arquivo: `backend/main.py`

Rota: `POST /chat`

Entrada `MensagemRequest`:

- `mensagem`
- `session_id`
- `pesquisar_web`
- `project_id`

Saída `MensagemResponse`:

- `resposta`
- `session_id`
- `project_id`
- `fontes`
- `tempo_total`
- `tokens_gerados`
- `provider_used`
- `fallback_reason`
- `provider_configured`
- `model`
- `latency_ms`
- `agent_trace`

### 6.2 Fluxo de `/chat`

1. valida `cerebro`;
2. cria/reutiliza sessão;
3. carrega histórico;
4. carrega memórias do projeto;
5. busca quando habilitada;
6. salva mensagem do usuário;
7. carrega memória interna;
8. acrescenta lições operacionais;
9. chama `cerebro.pensar`;
10. executa agentes internos;
11. salva resposta;
12. grava evento de memória;
13. devolve resposta e telemetria.

A integração multi-IA deve ocorrer dentro de `CerebroIA`, preservando `backend/main.py`.

## 7. Cérebro e fallback legado

Arquivo: `backend/cerebro.py`

Classe: `CerebroIA`

Contrato:

```python
async def pensar(
    pergunta: str,
    contexto_busca: str = '',
    historico: list[dict] | None = None,
    max_tokens: int | None = None,
) -> tuple[str, int, float]
```

Retorno: texto, tokens, latência em segundos.

Metadados usados:

- `provider`
- `nome_modelo`
- `last_provider_used`
- `last_fallback_reason`

Fallback padrão:

```text
gemini,openrouter,deepseek
```

Configuração atual:

- `AI_PROVIDER`
- `AI_PROVIDER_ORDER`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_API_URL`
- `AI_REVIEW_ENABLED`
- `AI_REVIEW_PROVIDER`
- `AI_REVIEW_TIMEOUT`

`scripts/32_test_fallback_order.py` valida Gemini→OpenRouter, Gemini→OpenRouter→DeepSeek, ordem personalizada e metadados. Esse fallback deve permanecer disponível.

## 8. Prompt e Watcher

`CerebroIA._construir_prompt` já define:

- identidade HelpUS;
- português do Brasil;
- proibição de identidade do modelo-base;
- recibos não são comandos;
- não inventar campos;
- JSON estrito;
- contratos `send_chat` e `run_command`;
- uso de `gateway-brain-supervisor`;
- proibição de marcadores de envelope dentro de `message`.

O roteador deve receber o mesmo prompt consolidado.

## 9. Memória

### 9.1 Projeto

`backend/main.py` usa `construir_contexto_memorias`, com limites e regra de que memória não substitui pergunta, política, autorização ou validação.

### 9.2 Interna

Leitura:

- `backend/helpus_memory_reader.py`
- flag `HELPUS_MEMORY_CONTEXT_ENABLED`
- limite padrão 8;
- filtro por conversa/projeto;
- falha retorna vazio.

Gravação:

- `backend/helpus_internal_memory_recorder.py`
- `safe_record_chat_memory_event`;
- falha não quebra o chat;
- sem promoção automática de feedback, lição ou regra.

O futuro cliente multi-IA não deve consultar o banco. Deve receber o contexto pronto.

## 10. Provedor local

`backend/local_ai_provider.py` é desligado por padrão, `analysis_only`, OpenAI-compatible, sem execução de comandos e controlado por `HELPUS_LOCAL_AI_*`. Não confundir com o roteador em nuvem.

## 11. Frontend

`frontend/src/app/page.tsx` envia `POST /chat` e já lê `provider_used`, `fallback_reason` e `agent_trace`. A primeira integração pode ser totalmente backend.

## 12. Arquivos críticos

- `backend/config.py`
- `backend/cerebro.py`
- `backend/main.py`
- `backend/local_ai_provider.py`
- `backend/helpus_memory_reader.py`
- `backend/helpus_internal_memory_recorder.py`
- `frontend/src/app/page.tsx`
- `scripts/32_test_fallback_order.py`
- `services/multi_ai_router/app.py`
- `services/multi_ai_router/router_core.py`

Ler os arquivos no commit atual. Não sobrescrever mudanças posteriores com base em hashes antigos.

## 13. Próxima fase recomendada

Criar integração opcional do runtime com o roteador.

Escopo sugerido:

1. `backend/multi_ai_provider.py`;
2. configuração em `backend/config.py`;
3. integração em `backend/cerebro.py`;
4. testes com mocks;
5. smoke de contrato;
6. scripts no `package.json`;
7. documentação;
8. commit e push.

Variáveis propostas:

- `HELPUS_MULTI_AI_ENABLED=false`
- `HELPUS_MULTI_AI_BASE_URL=http://127.0.0.1:8080`
- `HELPUS_MULTI_AI_API_KEY=`
- `HELPUS_MULTI_AI_TIMEOUT_SECONDS=180`
- `HELPUS_MULTI_AI_MODE=auto`
- `HELPUS_MULTI_AI_DEFAULT_ALIAS=helpus-general`
- `HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=true`

A flag deve permanecer desligada por padrão.

## 14. Comportamento alvo

Com flag desligada:

- não chamar roteador;
- preservar legado;
- preservar fallback;
- não exigir novas credenciais.

Com flag ligada:

1. construir o mesmo prompt HelpUS;
2. enviar ao roteador;
3. receber resposta e metadados;
4. atualizar `last_provider_used`;
5. atualizar `last_fallback_reason`;
6. atualizar `nome_modelo`;
7. retornar o contrato original.

Falha com `HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=true`:

- motivo sanitizado;
- executar legado;
- não expor chave, token, payload ou stack trace.

Fallback desligado:

- falhar explicitamente;
- erro sanitizado;
- não inventar resposta.

## 15. Endpoint de orquestração

```text
POST /v1/route
```

O cliente backend cuida de transporte, autenticação, timeout, parsing, normalização e sanitização. Alias, modo, revisão e conselho permanecem no roteador.

## 16. Testes obrigatórios

- flag desligada não chama roteador;
- sucesso multi-IA mockado;
- falha com fallback;
- timeout limitado;
- prompt contém identidade, Watcher, histórico, memória, busca e pergunta;
- nenhuma chamada externa real.

Regressão mínima:

```powershell
python scripts/32_test_fallback_order.py
python scripts/82_validate_multi_ai_foundation.py
python -m unittest discover -s tests -p 'test_multi_ai_router_core.py' -v
npm run smoke:providers
npm run test:fallback
git diff --check
```

## 17. Critérios de aceitação

- flag desligada por padrão;
- legado preservado;
- roteador só quando habilitado;
- fallback configurável;
- nenhuma credencial versionada;
- nenhum segredo em logs;
- nenhum executor de comandos;
- Watcher preservado;
- `ai-bridge-local` preservado;
- testes antigos e novos aprovados;
- escopo exato;
- commit e push;
- `HEAD == origin/main`;
- status limpo.

## 18. Proibições e limites

Não executar:

- `git reset --hard`;
- `git clean`;
- force push;
- impressão de `.env`;
- inclusão de segredo;
- alteração em `D:\dev\autocode\ai-bridge-local`;
- invenção de recibos;
- execução de comandos pelo roteador;
- promoção automática de memória;
- remoção do fallback legado;
- mudança de frontend sem necessidade.

## 19. Procedimento para o próximo chat

1. ler este documento;
2. executar `git fetch`;
3. verificar commit atual;
4. verificar se a integração já começou;
5. não reaplicar implementação existente;
6. criar backup externo;
7. limitar escopo;
8. rollback em falha anterior ao commit;
9. testar;
10. commit e push;
11. atualizar este handoff.

## 20. Estado final

- fundação multi-IA: concluída;
- integração do runtime: pendente;
- memória: integrada ao `/chat`;
- Watcher: regras existentes;
- fallback legado: testado;
- frontend: preparado para telemetria;
- GPU: não provisionada;
- credenciais: não adicionadas;
- AI Bridge Local: não alterado.
