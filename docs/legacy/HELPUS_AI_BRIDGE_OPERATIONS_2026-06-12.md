# HelpUS AI e AI Bridge Local - Responsabilidades e Evolução Operacional

Data: 2026-06-12

## Contexto

Este documento registra a divisão correta entre a aplicação HelpUS AI e a infraestrutura AI Bridge Local, após os testes de conversa entre chats, uso do watcher e tentativa de treinamento operacional da nossa IA particular.

## Divisão de responsabilidades

### HelpUS AI (`D:/dev/ai`)

A pasta `D:/dev/ai` contém a aplicação da nossa IA particular. Esta frente é responsável por evoluir a capacidade da HelpUS AI, incluindo:

- comportamento do assistente;
- prompt base e instruções operacionais;
- autenticação e rotas do backend;
- integração com provedores de IA;
- entendimento do protocolo AI Bridge Local;
- capacidade de pedir dados faltantes antes de montar comandos;
- autonomia gradual para interagir com outros chats e, quando autorizado, solicitar execuções locais.

Toda evolução da inteligência, do comportamento e da autossuficiência da HelpUS AI deve acontecer nesta frente.

### AI Bridge Local (`D:/dev/autocode/ai-bridge-local`)

A pasta `D:/dev/autocode/ai-bridge-local` contém a infraestrutura local de transporte e execução. Esta frente é responsável por:

- conversa entre chats;
- entrega de mensagens via extensão;
- gateway local;
- worker local;
- execução de comandos no computador quando solicitada por envelopes válidos;
- validação, enfileiramento, recibos e telemetria local.

Esta frente não deve ser alterada pela frente HelpUS AI sem coordenação com o chat responsável pelo AI Bridge Local.

## Aprendizado importante do incidente

Durante os testes, a HelpUS AI confundiu recibos/logs do watcher com comandos de entrada.

Exemplo de recibo/log, que não é comando:

```text
[AI_LOCAL] id=... resultado=pendente metodo=watcher status=enviando
```

Esse tipo de texto é apenas a saída da extensão ou do bridge. A HelpUS AI não deve simular esse formato.

Quando o usuário pedir para usar o watcher, a HelpUS AI deve entender que precisa produzir um comando válido para o AI Bridge Local, e não um log.

## Regra operacional para a HelpUS AI

Quando receber instrução explícita para usar watcher, bridge ou AI Bridge Local:

1. Não escrever logs como `[AI_LOCAL]`, `[AI_LOCAL_RUN]`, `resultado=pendente`, `status=enviando` ou `metodo=watcher`.
2. Não simular recibos.
3. Se for conversa entre chats, usar ação `send-chat-message`.
4. Se for execução local, usar ação `run-command` somente quando houver dados suficientes e autorização.
5. Usar `delivery_kind` correto:
   - `inter_agent_message` para conversa entre chats;
   - `local_capability` para execução local via gateway/worker.
6. Se faltarem dados obrigatórios, pedir os dados em texto comum.
7. Se for instruída a responder via bridge, responder somente com o envelope solicitado, sem explicações antes ou depois.
8. Usar JSON estrito, aspas duplas ASCII e evitar caracteres invisíveis.
9. Não colocar exemplos de marcadores de envelope dentro de campos de mensagem enviados para outra IA, pois a extensão pode interpretar esses marcadores como um novo comando.
10. Não inventar `source_chat_id`, `target_chat_id`, `command_id`, `cwd` ou comandos locais quando não estiverem claros.

## Diretriz de evolução

A HelpUS AI deve ser treinada para ficar cada vez mais autossuficiente, mas a evolução deve ocorrer na aplicação `D:/dev/ai`, principalmente no prompt base e nas camadas de instrução do backend.

A infraestrutura AI Bridge Local deve permanecer como ferramenta de transporte/execução. Ela não deve carregar regras específicas da HelpUS AI, exceto quando definido pelo chat responsável pelo projeto AI Bridge Local.

## Procedimento recomendado para próximos ajustes

1. Inspecionar o prompt atual da HelpUS AI em `backend/cerebro.py`.
2. Adicionar uma seção curta e objetiva sobre uso do AI Bridge Local.
3. Validar sintaxe Python e diff.
4. Testar uma conversa normal para garantir que a HelpUS AI continua respondendo como assistente comum.
5. Testar uma instrução controlada de uso do watcher.
6. Só depois de validar, commitar e publicar.

## Estado registrado

- A alteração experimental feita no AI Bridge Local para criar um modo simples foi revertida.
- O commit de remoção no AI Bridge Local foi `4aea3cf Remove simple bridge mode changes`.
- A versão do `extension/content_script.js` voltou para `0.4.36`.
- A evolução futura da HelpUS AI deve ocorrer no repo `D:/dev/ai`.
