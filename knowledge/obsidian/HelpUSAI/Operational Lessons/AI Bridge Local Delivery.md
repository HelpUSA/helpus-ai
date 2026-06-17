---
title: AI Bridge Local Delivery
source: helpusai
kind: operational_lesson
topic: ai_bridge_local_delivery
status: candidate
confidence: 0.75
created: 2026-06-17
tags:
  - helpusai
  - operational_lesson
  - watcher
  - ai_bridge_local
  - delivery
  - composer
---

# AI Bridge Local Delivery

Status: `candidate`

Topic: `ai_bridge_local_delivery`

Confidence: `0.75`

## Problema

O envio inter-chat pode falhar com submit_not_confirmed_composer_still_has_text quando o composer do destino fica com texto preso.

## Correção

Abrir a aba destino, limpar ou enviar manualmente o texto preso, confirmar extensao ativa e reenviar com command_id novo.

## Evidência

O envio send_helpusai_protocol_self_fix_20260616_001 falhou por composer ainda conter texto.

## Links

- [[Operational Lessons]]
- [[AI Bridge Local]]
- [[Watcher Protocol]]
