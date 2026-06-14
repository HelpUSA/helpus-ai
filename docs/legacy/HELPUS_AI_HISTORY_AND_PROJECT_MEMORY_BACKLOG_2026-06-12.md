# HelpUS AI - Backlog de historico, continuidade e memoria ativa

Data: 2026-06-12
Repo: D:/dev/ai

## Contexto

Durante a evolucao da HelpUS AI, foi identificado que a aplicacao precisa melhorar dois pontos importantes para uso por desenvolvedores:

1. permitir ver mensagens e conversas anteriores com mais clareza;
2. permitir continuar uma conversa existente sem cair sempre em uma nova conversa;
3. adicionar memoria ativa do projeto, para preservar fatos operacionais, decisoes e proximos passos.

## Estado atual observado

O backend ja possui base de historico:

- MensagemRequest aceita session_id e project_id.
- O endpoint /chat usa session_id existente ou cria um novo.
- Antes de responder, o backend tenta carregar historico da session_id.
- A conversa e salva na tabela conversas com user_email, title e project_id.
- Existem endpoints /conversas, /historico/{session_id} e DELETE /conversa/{session_id}.

O frontend tambem ja possui partes relevantes:

- estado sessionId;
- lista conversas;
- carregarConversas;
- carregarHistorico;
- URL /c/{sessionId};
- botao Nova conversa;
- busca de chats;
- indicador de historico ativo.

Portanto, a proxima etapa nao e criar historico do zero. A etapa correta e melhorar a UX de continuidade, criar smokes especificos e adicionar memoria ativa do projeto.

## Atividade 1 - Continuidade de conversas anteriores

Objetivo: o usuario deve conseguir abrir uma conversa anterior, ver as mensagens ja feitas e continuar exatamente na mesma session_id.

Requisitos:

- abrir /c/{sessionId} deve carregar historico automaticamente;
- clicar em conversa recente deve carregar historico e manter session_id ativa;
- enviar nova mensagem depois de carregar historico deve usar a mesma session_id;
- botao Nova conversa deve ser claro e separado de continuar conversa;
- interface deve mostrar claramente qual conversa esta ativa;
- se o historico falhar, mostrar erro amigavel e manter opcao de tentar novamente;
- mobile deve ter acesso claro a chats recentes.

Validacoes desejadas:

- criar conversa nova;
- confirmar que aparece em /conversas;
- abrir /c/{session_id};
- confirmar que /historico/{session_id} retorna mensagens;
- enviar nova mensagem com a mesma session_id;
- confirmar que a conversa continua e nao cria nova session_id.

## Atividade 2 - Memoria ativa do projeto

Objetivo: criar uma camada persistente de memoria de projeto para desenvolvedores, separada do historico comum de conversas.

Essa memoria deve guardar fatos e decisoes como:

- divisao de responsabilidades entre HelpUS AI e AI Bridge Local;
- regras operacionais do watcher;
- IDs importantes quando apropriado;
- preferencias de desenvolvimento;
- estado atual das frentes;
- proximas atividades;
- decisoes tomadas pelo usuario;
- cuidados e restricoes para nao repetir erros.

Requisitos iniciais:

- tabela propria, por exemplo project_memories;
- campos sugeridos:
  - id;
  - project_id;
  - title;
  - content;
  - tags;
  - enabled;
  - created_at;
  - updated_at;
  - created_by;
- endpoints autenticados:
  - listar memorias;
  - criar memoria;
  - editar memoria;
  - desativar memoria;
  - buscar memorias por projeto/tag;
- painel no frontend para desenvolvedores verem e editarem memorias;
- uso controlado no prompt da HelpUS AI:
  - incluir somente memorias enabled;
  - limitar tamanho;
  - priorizar project_id atual;
  - deixar claro que memoria de projeto e contexto operacional, nao ordem absoluta.

## Cuidados

- memoria ativa nao deve substituir auditoria em Git/docs;
- memoria nao deve armazenar segredos, tokens, senhas ou credenciais;
- deve haver forma de editar/desativar memoria incorreta;
- deve haver separacao por usuario/projeto quando necessario;
- toda mudanca de comportamento sensivel deve continuar documentada em docs e commits.

## Ordem recomendada

1. Criar smoke/inspecao da continuidade de historico existente.
2. Corrigir UX de continuar conversa, se necessario.
3. Criar documentacao tecnica da memoria ativa.
4. Implementar backend da memoria ativa.
5. Implementar frontend da memoria ativa.
6. Integrar memoria ativa ao prompt com limite e filtros.
7. Criar smokes de memoria ativa.
8. Deploy controlado.

## Estado

Backlog registrado. Nenhuma alteracao de codigo foi aplicada neste documento.