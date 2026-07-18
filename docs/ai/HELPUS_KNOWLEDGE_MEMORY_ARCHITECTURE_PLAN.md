# AI HelpUS — Plano de Arquitetura de Conhecimento e Memória Persistente

Atualizado: 2026-07-17
Status: planejamento aprovado
Repositório: `HelpUSA/helpus-ai`
Diretório local: `D:/dev/ai`

## 1. Decisão de escopo

Toda a implementação descrita neste documento pertence ao AI HelpUS.

`ai-bridge-local` é uma aplicação externa de transporte e execução. Ela não
será alterada neste projeto para fornecer memória, conhecimento, prompts,
recuperação, administração ou comportamento específico do AI HelpUS.

O AI HelpUS continuará emitindo envelopes compatíveis com a infraestrutura
externa, mas manterá internamente:

- identidade e instruções permanentes;
- memória persistente;
- conhecimento documental;
- recuperação contextual;
- continuidade das conversas;
- montagem do contexto;
- administração e auditoria.

## 2. Padrão observado em chats convencionais

Assistentes existentes não costumam retreinar o modelo sempre que recebem um
novo documento ou uma preferência do usuário.

O padrão utilizado combina mecanismos especializados:

1. instruções permanentes ou personalizadas;
2. memórias salvas;
3. conhecimento isolado por projeto;
4. recuperação de trechos de documentos;
5. resumos de conversas anteriores;
6. ferramentas para fatos atuais ou variáveis.

O AI HelpUS adotará a mesma separação.

## 3. Arquitetura em cinco camadas

### 3.1 Regras permanentes do agente

Regras críticas devem ser inseridas em todas as chamadas ao modelo e não podem
depender de busca semântica.

Exemplos:

- identidade e finalidade do AI HelpUS;
- segurança e autorização;
- protocolo do Watcher;
- formato dos envelopes;
- interpretação de eventos intermediários e finais;
- proibição de inventar recibos;
- separação entre AI HelpUS e `ai-bridge-local`.

Arquivos sugeridos:

- `backend/prompts/system/agent_identity.md`
- `backend/prompts/system/safety_policy.md`
- `backend/prompts/system/watcher_operational_protocol.md`
- `backend/prompts/system/result_semantics.md`

Regra operacional obrigatória:

AI HelpUS utiliza o Watcher emitindo um envelope válido em sua própria resposta.
A infraestrutura externa captura e executa o envelope. O agente não deve
recusar uma solicitação segura apenas porque está sendo executado dentro de uma
interface de chat.

### 3.2 Memória persistente estruturada

Memórias devem representar fatos curtos e reutilizáveis, por exemplo:

- idioma preferido;
- shell preferido;
- formato de resposta preferido;
- limites explícitos de um projeto;
- instruções recorrentes aprovadas;
- fatos verificados da organização.

Escopos previstos:

- `global`
- `organization:<id>`
- `agent:helpus`
- `user:<id>`
- `project:<id>`
- `conversation:<id>`

Campos mínimos:

- identificador;
- organização;
- usuário;
- projeto;
- conversa;
- escopo;
- chave;
- valor;
- tipo e referência da origem;
- confiança;
- importância;
- status;
- criação e atualização;
- expiração.

Operações necessárias:

- propor;
- aprovar;
- rejeitar;
- atualizar;
- desativar;
- excluir;
- expirar;
- detectar conflitos;
- auditar.

### 3.3 Conhecimento documental com RAG

Documentos longos devem ser indexados e recuperados por relevância.

Fluxo planejado:

1. cadastro da fonte;
2. extração do conteúdo;
3. normalização;
4. divisão em trechos;
5. metadados e hash;
6. índice textual;
7. embeddings;
8. busca híbrida;
9. reranking;
10. inclusão dos melhores trechos no contexto.

A busca deve aplicar primeiro:

- organização e tenant;
- projeto;
- domínio;
- permissões;
- status da fonte.

Depois deve combinar:

- busca textual;
- busca vetorial;
- confiança da fonte;
- atualidade;
- remoção de duplicatas;
- reranking.

PostgreSQL com busca textual e `pgvector` é a direção preferencial de produção,
desde que compatível com a infraestrutura já implantada.

### 3.4 Continuidade das conversas

Conversas longas devem combinar:

- janela limitada de mensagens recentes;
- resumo progressivo das mensagens antigas;
- decisões extraídas;
- fatos verificados;
- tarefas pendentes;
- resultados confirmados;
- questões ainda abertas.

O resumo não será tratado automaticamente como fonte autoritativa. Fatos
importantes devem preservar sua origem antes de virar memória persistente.

### 3.5 Ferramentas e estado atual

Dados variáveis não devem ser gravados como conhecimento permanente.

Exemplos:

- PID atual;
- profundidade atual da fila;
- estado de um serviço;
- deployment atual;
- preços;
- legislação atual;
- agenda;
- resultado temporário de comando.

A base pode explicar como obter esses dados, mas o valor atual deve vir de uma
ferramenta, API, consulta ou recibo final.

## 4. Montagem determinística do contexto

Ordem planejada:

1. identidade e política permanente;
2. protocolo operacional obrigatório;
3. identificadores dinâmicos da execução;
4. memórias relevantes;
5. conhecimento relevante da organização e do projeto;
6. resumo da conversa;
7. mensagens recentes;
8. mensagem atual do usuário.

Identificadores como `current_chat_id`, `conversation_id`, PID e estado atual
não são memórias. Eles devem ser fornecidos dinamicamente pela aplicação e não
podem ser inventados pelo modelo.

O context builder deverá controlar:

- orçamento de tokens por camada;
- ordem determinística;
- permissões antes da busca;
- duplicidade;
- versão dos prompts;
- versão dos índices;
- rastreabilidade dos itens incluídos.

## 5. Semântica permanente do Watcher

O AI HelpUS deve conhecer permanentemente:

- ele emite o envelope;
- a infraestrutura externa executa;
- `source_chat_id` vem do contexto atual;
- `status=queued` é intermediário;
- entrega confirmada não prova execução local;
- `AI_LOCAL_RUN` com `result_is_final=1` é resultado final;
- sucesso depende de `success`, `return_code`, stdout, stderr e contrato;
- JSON inválido exige correção e novo `command_id`;
- recibos nunca podem ser inventados;
- operações destrutivas exigem autorização e validação de segurança.

Nenhuma alteração em `ai-bridge-local` faz parte deste programa.

## 6. Evolução da memória já existente

As estruturas existentes continuam válidas:

- `helpus_memory_events`
- `helpus_memory_feedback`
- `helpus_memory_lessons`
- `helpus_memory_rules`

A evolução poderá acrescentar:

- `helpus_agent_prompts`
- `helpus_memories`
- `helpus_memory_audit`
- `helpus_knowledge_sources`
- `helpus_knowledge_documents`
- `helpus_knowledge_chunks`
- `helpus_knowledge_embeddings`
- `helpus_conversation_summaries`
- `helpus_conversation_facts`
- `helpus_retrieval_events`
- `helpus_context_build_events`

Este documento não autoriza migration automática.

## 7. Política de escrita da memória

O modelo não gravará qualquer frase diretamente na memória permanente.

Fluxo obrigatório:

1. extração de candidato;
2. classificação;
3. verificação de sensibilidade;
4. verificação da origem;
5. detecção de conflito;
6. política de aprovação;
7. persistência;
8. registro de auditoria.

Regras:

- preferências explícitas podem ser propostas automaticamente;
- fatos inferidos exigem confirmação;
- resultados de ferramentas exigem recibo final real;
- dados temporários recebem TTL ou não são persistidos;
- tokens, credenciais e segredos não viram memórias gerais;
- conflitos não são sobrescritos silenciosamente;
- toda alteração deve ser reversível e auditável.

## 8. Administração

A interface administrativa deverá permitir:

### Memória

- ativar e desativar;
- listar;
- inspecionar origem, confiança, escopo e expiração;
- aprovar e rejeitar propostas;
- editar;
- desativar;
- excluir;
- consultar auditoria.

### Conhecimento

- cadastrar ou enviar fontes;
- atribuir organização, projeto e domínio;
- visualizar processamento e indexação;
- visualizar trechos;
- reindexar;
- substituir versão;
- desativar;
- excluir;
- testar recuperação;
- identificar os trechos usados em uma resposta.

### Agente

- consultar versões dos prompts;
- visualizar contexto montado;
- executar testes de regressão;
- comparar comportamento antes e depois de alterações.

## 9. Programa de implementação

### KM-1 — Bootstrap operacional permanente

- prompts versionados de identidade, segurança, Watcher e resultados;
- identificadores da conversa fornecidos dinamicamente;
- teste que reproduz a recusa observada;
- comprovação de emissão correta do envelope.

### KM-2 — Domínio e API de memória

- registros estruturados;
- escopo, origem, confiança, expiração e auditoria;
- listar, propor, aprovar, rejeitar, atualizar, desativar e excluir;
- preservar o trabalho existente de eventos, feedback, lições e regras.

### KM-3 — Continuidade das conversas

- resumos progressivos;
- decisões, fatos, tarefas e resultados;
- histórico recente limitado;
- atualização e invalidação de resumos.

### KM-4 — Ingestão de conhecimento

- cadastro de fontes;
- extração;
- normalização;
- chunking;
- metadados;
- hashes;
- estado da ingestão;
- índice textual.

### KM-5 — Recuperação híbrida

- embeddings;
- busca vetorial;
- busca textual;
- filtros de permissões;
- reranking;
- proveniência.

### KM-6 — Context builder

- ordem determinística;
- orçamento de tokens;
- remoção de duplicatas;
- registro de versões;
- visualização e diagnóstico.

### KM-7 — Interface administrativa

- administração de memória;
- administração de fontes;
- testes de recuperação;
- versões de prompts;
- auditoria.

### KM-8 — Avaliação e produção

- perguntas fixas de benchmark;
- precisão e recall;
- regressão de prompts;
- isolamento entre tenants e projetos;
- testes contra envenenamento de memória;
- latência e custo de tokens;
- rollback e reindexação.

## 10. Testes de aceitação

O programa somente estará concluído quando comprovar que:

1. após reiniciar a aplicação, o agente ainda sabe emitir envelopes;
2. uma solicitação segura gera envelope, não uma falsa recusa;
3. `queued` é tratado como intermediário;
4. sucesso só é declarado após recibo final real;
5. JSON inválido é corrigido com novo identificador;
6. preferência explícita sobrevive a outra conversa;
7. conhecimento de um projeto não vaza para outro;
8. memória excluída ou desativada não é injetada;
9. versão nova de documento substitui a antiga;
10. recuperação informa fonte e trecho corretos;
11. afirmação falsa de conversa não substitui documento curado;
12. segredos e dados temporários não são persistidos;
13. contexto respeita o limite de tokens;
14. administradores conseguem auditar cada item utilizado.

## 11. Não objetivos

Este planejamento não:

- altera `ai-bridge-local`;
- retreina o modelo-base;
- executa migrations;
- ativa embeddings em produção;
- transforma todas as mensagens em memória;
- concede acesso direto do modelo ao computador;
- trata resumos como fatos autoritativos;
- armazena credenciais ou estado temporário como memória permanente.

## 12. Referências pesquisadas

Documentações oficiais consideradas:

- OpenAI Help Center — Memory FAQ:
  `https://help.openai.com/articles/8590148-memory-faq`
- OpenAI Help Center — Projects in ChatGPT:
  `https://help.openai.com/en/articles/10169521-projects-in-chatgpt`
- Anthropic Help Center — RAG for Projects:
  `https://support.anthropic.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects`
- Anthropic Help Center — Projects:
  `https://support.anthropic.com/en/articles/9519177-how-can-i-create-and-manage-projects`
- Google Gemini Apps Help — Gems:
  `https://support.google.com/gemini/answer/15235603`
- Microsoft Support — Copilot Memory:
  `https://support.microsoft.com/en-us/microsoft-365-copilot/manage-copilot-memory-in-microsoft-365-copilot`
- Microsoft Support — Copilot Notebooks:
  `https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-microsoft-365-copilot-notebooks`

## 13. Resultado aprovado

- comportamento crítico: prompts permanentes;
- preferências: memória estruturada;
- documentos: RAG isolado por escopo;
- conversas longas: resumo e fatos extraídos;
- dados atuais: ferramentas e recibos;
- governança: administração e auditoria.

Toda a implementação permanecerá dentro do AI HelpUS.

<!-- AI_HELPUS_MANAGED:MULTI_AI_RELATIONSHIP_20260718:START -->


## Multi-model execution relationship — 2026-07-18

Multi-model routing is downstream from trusted context assembly. Permanent
rules, Watcher semantics, dynamic runtime identifiers, memory, knowledge,
conversation summaries and recent messages are assembled before route
selection.

All specialists receive the same critical rules. No model may invent an
execution receipt or dynamic runtime identifier.

Architecture: `docs/ai/HELPUS_MULTI_AI_CLOUD_ARCHITECTURE.md`.

<!-- AI_HELPUS_MANAGED:MULTI_AI_RELATIONSHIP_20260718:END -->

<!-- AI_HELPUS_MANAGED:MULTI_AI_MEMORY_CONTINUATION_2026_07_18:START -->

## Continuidade da memória na integração multi-IA

`/chat` já monta histórico, memória de projeto, memória interna, busca, lições e pergunta antes de chamar `CerebroIA.pensar`.

O futuro `backend/multi_ai_provider.py` não deve consultar o banco. Deve receber o prompt consolidado, evitando duplicidade, divergência de filtros e acoplamento do gateway.

A gravação permanece em `safe_record_chat_memory_event`, com o provedor usado. Não promover automaticamente eventos para feedback, lição ou regra.

<!-- AI_HELPUS_MANAGED:MULTI_AI_MEMORY_CONTINUATION_2026_07_18:END -->
