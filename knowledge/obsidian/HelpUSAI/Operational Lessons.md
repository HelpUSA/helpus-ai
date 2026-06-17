---
title: Operational Lessons
source: helpusai
kind: obsidian_note
created: 2026-06-17
tags:
  - helpusai
  - lessons
  - operations
---

# Operational Lessons

## Conceito

Operational lessons são lições candidatas extraídas de erros, correções, smokes e uso real.

Fluxo recomendado:

1. evento operacional acontece;
2. HelpUSAI registra o problema;
3. HelpUSAI registra a correção;
4. a lição fica como candidate;
5. após validação, pode virar regra promovida.

## Lições iniciais

### AI Bridge Local inter-chat

Problema: a HelpUSAI confundiu protocolo de mensagem entre chats e misturou explicação com envelope.

Correção: para mensagem entre chats usar `send-chat-message`, `inter_agent_message`, `source_chat_id`, `target_chat_id`, `message` no topo do JSON, `payload_json` vazio e `no_reply` conforme necessário.

Evidência: o envio `send_helpusai_simple_supervisor_test_20260616_009` chegou ao chat da HelpUSAI e ela respondeu `RECEBIDO_HELPUSAI_SUPERVISOR_009` no chat destino.

### Envelope parse error

Problema: o watcher pode tentar interpretar explicações como JSON quando exemplos com marcadores reais aparecem no chat observado.

Correção: quando quiser executar, emitir somente o envelope puro. Quando quiser explicar, evitar marcadores reais e usar nomes substitutos.

### Composer preso

Problema: `submit_not_confirmed_composer_still_has_text` indica que o texto ficou no composer do chat destino.

Correção: abrir a aba destino, limpar ou enviar o texto preso, confirmar a extensão ativa e reenviar com `command_id` novo.
