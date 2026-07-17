# HelpUSAI Operational Context Card

Updated: 2026-06-15

## Purpose

This card gives HelpUSAI the minimum operational context required before it proposes commands, patches, smokes, documentation updates, commits, or deployment-related actions.

HelpUSAI must not invent files, commands, smokes, repository paths, or safety rules when this card provides the expected values.

## Context

- Assistant: HelpUSAI
- Project: HelpUSAI
- Repo: D:/dev/ai
- Environment: Windows / PowerShell
- Current micro: Micro 13 - operational context card
- Previous micro: Micro 12 - readonly operator dashboard summary completed

## Default readonly inspection

Use this before any patch:

- git status -sb
- git status -s
- git log --oneline --decorate -8
- git diff --stat

## Micro 13 allowed files

- docs/HELPUS_OPERATIONAL_CONTEXT_CARD.md
- backend/helpus_operational_context_card.py
- scripts/watcher/smoke_helpus_operational_context_card.py
- docs/HELPUS_PROJECT_MASTER.md

## Required smokes

- python -m py_compile backend/helpus_operational_context_card.py scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- git diff --check

## Safety restrictions

HelpUSAI must not propose or execute deploy, external network calls, git reset, git clean, destructive deletion, automatic rule activation, public API exposure, unbounded recursive scans, huge inline commands, or hidden scripts.

## Response rules

When asked for a command plan, HelpUSAI must answer with repo, current micro, readonly command, allowed files, required smokes, safety restrictions, and stop condition.

If context is unknown, HelpUSAI must ask for this Operational Context Card instead of inventing details.

## Stop condition

If any command fails, stop immediately and report step name, stdout summary, stderr summary, files touched, and next safe action.

<!-- AI_HELPUS_MANAGED:KNOWLEDGE_SCOPE_BOUNDARY_20260717:START -->

## Limite do produto para conhecimento e memória

O AI HelpUS é responsável por seus prompts, instruções operacionais, memória,
conhecimento, recuperação, resumos, montagem de contexto, administração e
auditoria.

`ai-bridge-local` é uma aplicação externa utilizada por meio do contrato de
envelopes já existente. Nenhuma alteração específica do AI HelpUS será exigida
nesse repositório.

Identificadores da conversa, PID, fila e estado de serviços são informações
dinâmicas, não memórias permanentes.

Plano canônico:

`docs/ai/HELPUS_KNOWLEDGE_MEMORY_ARCHITECTURE_PLAN.md`

<!-- AI_HELPUS_MANAGED:KNOWLEDGE_SCOPE_BOUNDARY_20260717:END -->
