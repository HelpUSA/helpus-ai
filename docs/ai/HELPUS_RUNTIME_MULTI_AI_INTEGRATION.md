# HelpUS — integração opcional do runtime multi-IA

Data da integração: 2026-07-20.

## 1. Objetivo

Integrar o roteador multi-IA existente ao runtime do HelpUS sem modificar o contrato público de `CerebroIA.pensar`, sem alterar `backend/main.py` e sem mudar o comportamento legado quando a funcionalidade estiver desligada.

## 2. Arquitetura

O fluxo público continua:

`POST /chat -> CerebroIA.pensar`

A integração fica inteiramente dentro de `CerebroIA`.

`backend/main.py` continua sem importar ou chamar diretamente o cliente multi-IA.

### Flag desligada

Com:

`HELPUS_MULTI_AI_ENABLED=false`

o método público delega diretamente para `_pensar_legado`.

Nesse estado:

- nenhuma chamada é feita ao roteador;
- o prompt legado é preservado;
- os providers legados são preservados;
- a ordem de fallback permanece `gemini,openrouter,deepseek`;
- o retorno permanece `(text, tokens, latency_seconds)`.

### Flag ligada

Com:

`HELPUS_MULTI_AI_ENABLED=true`

o prompt consolidado do HelpUS é enviado para:

`POST /v1/chat/completions`

O payload utiliza:

- `model`: alias configurado;
- `messages`: prompt consolidado;
- `max_tokens`;
- `temperature`;
- `stream=false`;
- `helpus_mode`: modo de orquestração.

## 3. Configuração

| Variável | Padrão |
|---|---|
| `HELPUS_MULTI_AI_ENABLED` | `false` |
| `HELPUS_MULTI_AI_BASE_URL` | `http://127.0.0.1:8080` |
| `HELPUS_MULTI_AI_API_KEY` | vazio |
| `HELPUS_MULTI_AI_TIMEOUT_SECONDS` | `180` |
| `HELPUS_MULTI_AI_MODE` | `auto` |
| `HELPUS_MULTI_AI_FALLBACK_TO_LEGACY` | `true` |
| `HELPUS_MULTI_AI_DEFAULT_ALIAS` | `helpus-general` |

Modos aceitos:

- `single`;
- `review`;
- `council`;
- `auto`.

Aliases aceitos pelo cliente runtime:

- `helpus-fast`;
- `helpus-general`;
- `helpus-reasoner`;
- `helpus-code`;
- `helpus-vision`;
- `helpus-verifier`;
- `helpus-embedding`.

O alias `helpus-embedding` é destinado principalmente às operações de embedding, mas permanece reconhecido pelo contrato de aliases do runtime.

## 4. Contrato público preservado

A assinatura pública permanece:

`pensar(self, pergunta, contexto_busca="", historico=None, max_tokens=None)`

O retorno permanece:

`(text, tokens, latency_seconds)`

A implementação anterior foi preservada em:

`_pensar_legado`

## 5. Prompt consolidado

O roteador recebe o mesmo prompt construído por `_construir_prompt`.

Continuam preservados:

- identidade pública HelpUS;
- contexto de busca;
- histórico;
- pergunta atual;
- regras operacionais do AI Bridge Local;
- `[AI_LOCAL]`;
- `[AI_LOCAL_RUN]`;
- `inter_agent_message`;
- `gateway-brain-supervisor`;
- `result_is_final=1`.

A integração não cria uma segunda versão do prompt.

## 6. Tratamento de falhas

Os motivos expostos pelo cliente são sanitizados.

Exemplos:

- `multi_ai_timeout`;
- `multi_ai_network_error`;
- `multi_ai_http_error`;
- `multi_ai_invalid_json`;
- `multi_ai_invalid_response`;
- `multi_ai_empty_response`;
- `multi_ai_unavailable`.

Quando:

`HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=true`

uma falha do roteador retorna ao caminho legado.

Quando:

`HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=false`

o runtime gera um erro explícito com código sanitizado.

Mensagens internas, payloads privados, chaves e tokens não são incluídos no erro público.

## 7. Telemetria interna

O objeto `CerebroIA` mantém:

- `last_provider_used`;
- `last_fallback_reason`;
- `last_multi_ai_alias`;
- `last_multi_ai_mode`;
- `last_multi_ai_request_id`;
- `last_multi_ai_latency_ms`.

Esses campos não alteram o contrato público de `pensar`.

## 8. Limites de responsabilidade

`backend/multi_ai_provider.py` realiza apenas a chamada HTTP ao roteador.

O cliente não:

- acessa banco de dados;
- acessa memória ou RAG;
- acessa Redis;
- executa comandos;
- modifica arquivos de negócio;
- altera o AI Bridge Local;
- provisiona GPU;
- adiciona credenciais.

## 9. Validação

Teste permanente:

`python -B -m unittest discover -s tests -p "test_multi_ai_runtime_integration.py" -v`

Validador consolidado:

`python -B scripts/83_validate_multi_ai_runtime.py`

Regressão da ordem de fallback:

`python -B scripts/32_test_fallback_order.py`

Validação da fundação multi-IA:

`python -B scripts/82_validate_multi_ai_foundation.py`

Testes do núcleo do roteador:

`python -B -m unittest tests/test_multi_ai_router_core.py -v`

Todos os testes específicos desta integração utilizam mocks e não fazem chamadas externas reais.

## 10. Estado desta entrega

- integração opcional no `CerebroIA`: concluída;
- comportamento desligado por padrão: preservado;
- fallback legado: preservado;
- contrato público: preservado;
- `backend/main.py`: não alterado;
- frontend: não alterado;
- memória e RAG: não alterados;
- Watcher: não alterado;
- `ai-bridge-local`: não alterado;
- credenciais: não adicionadas;
- GPU: não provisionada.

Marcadores finais:

- `CLOUD_GPU_PROVISIONED=False`;
- `PROVIDER_CREDENTIALS_ADDED=False`;
- `AI_BRIDGE_LOCAL_MODIFIED=False`.

<!-- HELPUS_RUNTIME_CLOUD_STATUS_START -->

## Estado cloud

A integração foi publicada no commit `cb917bec48a73d44dfceb2c038738cd429a32134`.

`http://127.0.0.1:8080` é somente o padrão de desenvolvimento local.

Em produção, o backend deverá usar o DNS privado do Railway:

`http://multi-ai-router.railway.internal:8080`

Durante a implantação:

- `HELPUS_MULTI_AI_ENABLED=false`;
- `HELPUS_MULTI_AI_FALLBACK_TO_LEGACY=true`.

Após os testes cloud, ativar `HELPUS_MULTI_AI_ENABLED=true`.

<!-- HELPUS_RUNTIME_CLOUD_STATUS_END -->
