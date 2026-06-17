---
title: AI Bridge Local Run Command
source: helpusai
kind: operational_lesson
topic: ai_bridge_local_run_command
status: candidate
confidence: 0.75
created: 2026-06-17
tags:
  - helpusai
  - operational_lesson
  - watcher
  - ai_bridge_local
  - run_command
---

# AI Bridge Local Run Command

Status: `candidate`

Topic: `ai_bridge_local_run_command`

Confidence: `0.75`

## Problema

Comandos locais usam protocolo diferente de mensagens entre chats.

## Correção

Para comando local, usar action/type run-command, delivery_kind local_capability, target_chat_id gateway-brain-supervisor e payload com cwd, timeout_seconds e command ou script_text/script_ext.

## Evidência

O gateway aceitou run-command em ciclos anteriores quando o payload ficou dentro do formato esperado.

## Links

- [[Operational Lessons]]
- [[AI Bridge Local]]
- [[Watcher Protocol]]
