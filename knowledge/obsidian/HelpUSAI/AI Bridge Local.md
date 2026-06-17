---
title: AI Bridge Local
source: helpusai
kind: obsidian_note
created: 2026-06-17
tags:
  - helpusai
  - ai_bridge_local
  - watcher
---

# AI Bridge Local

## Papel

AI Bridge Local é a ponte local que permite comunicação entre chats e execução de comandos locais controlados.

Na arquitetura atual:

- HelpUSAI é o cérebro operacional;
- AI Bridge Local é a ponte/executor;
- watcher/extensão observa chats;
- gateway local enfileira comandos;
- worker supervisor executa comandos locais quando aplicável.

## Usos principais

- enviar mensagens entre chats;
- executar comandos locais via `run-command`;
- retornar `AI_LOCAL`, `AI_LOCAL_RUN` ou `AI_LOCAL_ERRO`;
- permitir supervisão entre agentes.

## Diferença crítica

Mensagem entre chats não é comando local.

Mensagem entre chats usa `send-chat-message`.
Comando local usa `run-command`.
