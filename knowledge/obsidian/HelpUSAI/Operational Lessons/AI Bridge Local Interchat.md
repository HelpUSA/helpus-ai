---
title: AI Bridge Local Interchat
source: helpusai
kind: operational_lesson
topic: ai_bridge_local_interchat
status: candidate
confidence: 0.85
created: 2026-06-17
tags:
  - helpusai
  - operational_lesson
  - watcher
  - ai_bridge_local
  - interchat
  - send_chat_message
---

# AI Bridge Local Interchat

Status: `candidate`

Topic: `ai_bridge_local_interchat`

Confidence: `0.85`

## Problema

A HelpUSAI confundiu o protocolo de envio entre chats e misturou explicacoes com envelope.

## Correção

Para mensagem entre chats, usar send-chat-message, delivery_kind inter_agent_message, source_chat_id, target_chat_id, message no topo, payload_json vazio e no_reply conforme necessario. O envelope deve sair sozinho, sem explicacao.

## Evidência

O envio send_helpusai_simple_supervisor_test_20260616_009 chegou ao chat da HelpUSAI e ela respondeu RECEBIDO_HELPUSAI_SUPERVISOR_009 no chat destino.

## Links

- [[Operational Lessons]]
- [[AI Bridge Local]]
- [[Watcher Protocol]]
