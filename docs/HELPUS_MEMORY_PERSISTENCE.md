# HelpUSAI Memory Persistence

Updated: 2026-06-15

## Purpose

HelpUSAI needs persistent memory so it can store and consult operational context, conversation events, feedback, draft lessons, and human-approved rules.

This document describes Micro 30: persistent memory schema, local store, and API router draft.

## Scope

Micro 30 adds:

- `backend/helpus_persistent_memory_schema.py`
- `backend/helpus_persistent_memory_store.py`
- `backend/helpus_persistent_memory_api.py`
- smoke tests for schema, store, and API payloads

## Safety boundaries

Micro 30 does not apply migrations to Railway Postgres.

Micro 30 does not wire the router into production automatically.

Micro 30 does not promote lessons into rules automatically.

Micro 30 keeps feedback, lessons, and rules in draft status by default.

## Tables planned

- `helpus_memory_events`
- `helpus_memory_feedback`
- `helpus_memory_lessons`
- `helpus_memory_rules`

## API draft

The router draft exposes the intended shape:

- `GET /helpus/memory/status`
- `GET /helpus/memory/recent`
- `POST /helpus/memory/feedback-draft`

Runtime wiring must happen in a later guarded micro after review.

## Next steps

1. Inspect current Railway Postgres schema from inside Railway or via TCP Proxy.
2. Add a reviewed production migration script.
3. Add guarded API wiring.
4. Add auth/admin protections before exposing memory endpoints.
5. Add real conversation event capture after the storage layer is validated.

<!-- AI_HELPUS_MANAGED:KNOWLEDGE_MEMORY_EVOLUTION_20260717:START -->

## Evolução planejada em 2026-07-17

O trabalho existente de eventos, feedback, lições e regras aprovadas permanece
válido.

A evolução completa está em:

`docs/ai/HELPUS_KNOWLEDGE_MEMORY_ARCHITECTURE_PLAN.md`

O AI HelpUS separará:

- regras permanentes obrigatórias;
- memórias estruturadas;
- conhecimento documental com RAG;
- resumos de conversa;
- fatos atuais obtidos por ferramentas e recibos.

Memórias terão escopo, origem, confiança, ciclo de vida e auditoria.

Toda a implementação pertence a `HelpUSA/helpus-ai`. A aplicação externa
`ai-bridge-local` não será modificada por este programa.

<!-- AI_HELPUS_MANAGED:KNOWLEDGE_MEMORY_EVOLUTION_20260717:END -->
