---
title: AI Bridge Local Envelope
source: helpusai
kind: operational_lesson
topic: ai_bridge_local_envelope
status: candidate
confidence: 0.8
created: 2026-06-17
tags:
  - helpusai
  - operational_lesson
  - watcher
  - ai_bridge_local
  - envelope
  - json
---

# AI Bridge Local Envelope

Status: `candidate`

Topic: `ai_bridge_local_envelope`

Confidence: `0.8`

## Problema

O watcher pode tentar parsear explicacoes ou exemplos como JSON quando marcadores reais aparecem no chat observado.

## Correção

Quando quiser executar, emitir somente o envelope puro. Quando quiser explicar, evitar marcadores reais e usar nomes substitutos como marcador de inicio e marcador de fim.

## Evidência

Erros envelope_parse_error ocorreram quando texto explicativo, exemplos e fontes foram copiados junto do envelope.

## Links

- [[Operational Lessons]]
- [[AI Bridge Local]]
- [[Watcher Protocol]]
