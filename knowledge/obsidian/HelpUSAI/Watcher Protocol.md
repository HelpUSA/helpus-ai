---
title: Watcher Protocol
source: helpusai
kind: obsidian_note
created: 2026-06-17
tags:
  - helpusai
  - watcher
  - protocol
---

# Watcher Protocol

## Mensagem entre chats

Usar quando um chat precisa falar com outro chat.

Campos essenciais:

- `version`
- `command_id`
- `action`: `send-chat-message`
- `type`: `send-chat-message`
- `delivery_kind`: `inter_agent_message`
- `source_chat_id`
- `target_chat_id`
- `conversation_id`
- `from_agent`
- `message`
- `payload_json`
- `no_reply`

## Comando local

Usar quando precisa executar algo no computador local.

Campos essenciais:

- `action`: `run-command`
- `type`: `run-command`
- `delivery_kind`: `local_capability`
- `target_chat_id`: `gateway-brain-supervisor`
- `payload.cwd`
- `payload.timeout_seconds`
- `payload.command` ou `payload.script_ext` e `payload.script_text`

## Regras

- `command_id` deve ser único.
- Não misturar explicação com envelope.
- Para explicações, evitar marcadores reais.
- Para execução, emitir somente envelope puro.
