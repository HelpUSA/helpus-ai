---
type: project-status
project: HelpUSAI
area: ai-helpus
status: active
updated: 2026-07-04
tags:
 - helpusai
 - ai-helpus
 - obsidian
 - operational-lessons
 - roadmap
---

# HelpUSAI - Estado atual e direcao

## Fonte desta nota

Nota atualizada a partir de leitura readonly do repositorio D:/dev/ai, da pasta docs, da pasta reports e dos codigos principais da aplicacao.

## Estado atual

- Repositorio principal: D:/dev/ai.
- Head funcional observado: 8090c59 feat: add admin operational lessons panel.
- O repositorio estava limpo antes desta atualizacao documental.
- A aplicacao ja possui operational lessons, contexto operacional e exportacao relacionada a Obsidian.
- O painel admin readonly de operational lessons ja foi implementado e validado por smoke especifico.

## Componentes principais

| Area | Arquivo | Funcao |
|---|---|---|
| API principal | backend/main.py | Registra rotas e integra recursos do backend |
| Operational lessons | backend/helpus_operational_lessons.py | Mantem licoes operacionais usadas pela aplicacao |
| Contexto operacional | backend/helpus_operational_lesson_context.py | Injeta licoes relevantes no contexto interno |
| Exportacao Obsidian | backend/evolving_memory_obsidian_export.py | Apoia exportacao de memoria para notas |
| Admin | frontend/src/app/admin/page.tsx | Exibe painel administrativo e operational lessons |
| Smoke admin | scripts/helpusai/smoke_admin_operational_lessons_panel.py | Valida painel admin de lessons |

## Onde estamos

Estamos em fase de consolidacao. A base de memoria operacional ja existe, a exportacao para Obsidian ja existe, e o painel admin ja permite auditoria readonly. O foco agora e reduzir retrabalho e tornar a documentacao navegavel em notas pequenas.

## Para onde vamos

1. Manter docs em formato Obsidian dentro de docs/obsidian.
2. Criar notas pequenas por tema em vez de documentos gigantes.
3. Manter cada melhoria acompanhada de smoke especifico.
4. Atualizar roadmap depois de cada ciclo de trabalho.
5. Evitar dependencias externas instaveis sem necessidade real.

## Regras operacionais

- Sempre rodar git status -sb antes de editar.
- Nao usar git add ponto.
- Commitar apenas arquivos esperados.
- Rodar git diff --check antes de commit.
- Preferir script_text e script_ext em comandos longos do watcher.
- Para documentacao, usar frontmatter YAML e links internos Obsidian.

## Links internos

- [[README|Indice Obsidian HelpUSAI]]
- [[HELPUSAI_ROADMAP_OBSIDIAN|Roadmap operacional Obsidian]]
