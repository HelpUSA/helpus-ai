---
type: roadmap
project: HelpUSAI
area: ai-helpus
status: active
updated: 2026-07-04
tags:
 - helpusai
 - roadmap
 - obsidian
---

# HelpUSAI - Roadmap operacional Obsidian

## Principio

A aplicacao deve evoluir com pequenas alteracoes verificaveis. A documentacao em Obsidian deve explicar estado atual, decisao tomada e proximo passo.

## Agora

- Manter HelpUSAI limpo e validado.
- Usar o painel admin de operational lessons como ponto de auditoria.
- Manter exportacao e notas Obsidian apenas onde reduzem retrabalho.
- Nao integrar providers experimentais que possam virar dependencia instavel.

## Proximo ciclo

1. Revisar a experiencia do painel admin de operational lessons.
2. Conferir se as licoes exibidas sao as mesmas usadas no contexto operacional.
3. Adicionar smoke para qualquer nova rota ou transformacao de dados.
4. Atualizar esta nota ao final de cada ciclo.

## Backlog seguro

- Melhorar indice Obsidian.
- Criar checklist de release HelpUSAI.
- Criar relatorio de gaps de docs.
- Revisar dead letters somente em dry-run.

## Fora de escopo por enquanto

- Integrar NVIDIA NIM ou outro provider gratuito como dependencia da aplicacao.
- Fazer mudancas grandes em backend e frontend no mesmo commit sem smoke especifico.
- Usar dados sensiveis em endpoints experimentais.

## Links internos

- [[README|Indice Obsidian HelpUSAI]]
- [[HELPUSAI_STATUS_2026-07-04|Estado atual e direcao]]

## Checkpoint 2026-07-06 - Fase A Local Readonly API

Status: concluido e validado.

A API local read-only agora possui os blocos essenciais para diagnostico seguro do repositorio sem depender exclusivamente do watcher:

- `/local/status` para status Git resumido.
- `/local/diff` para diff/check read-only.
- `/local/files/read` para leitura segura de arquivo allowlisted.
- `/local/files/list` para listagem segura de arquivos allowlisted.
- `/local/docs/search` para busca segura em documentos locais.

Validacoes do checkpoint:

- Smoke local da API read-only passando.
- Build frontend passando.
- `git diff --check` limpo.
- Commit publicado: `ddd57bd feat: add local readonly file list and search`.

Proxima direcao: usar esses endpoints como base para uma UI/operador local de diagnostico, mantendo todas as acoes destrutivas fora da Fase A.

## Checkpoint 2026-07-06 - UI Admin Local Readonly

Status: concluido e validado.

Foi adicionada uma UI isolada em `/admin/local` para consumir os endpoints locais read-only da Fase A. A rota foi ligada ao painel `/admin` e recebeu smoke oficial via `npm run smoke:admin-local`.

Escopo entregue:

- Painel read-only para status Git local.
- Painel read-only para diff local.
- Listagem segura de `docs/`.
- Busca segura em `docs/`.
- Link de navegacao no admin principal.
- Smokes dedicados para painel e link.

Commits do checkpoint:

- `adf140f feat: add admin local readonly panel`
- `7538598 feat: link admin to local readonly panel`
- `97a75a1 test: add admin local readonly smoke script`

Proxima direcao: evoluir do diagnostico read-only para um operador de planejamento seguro, mantendo execucao real separada por gates explicitos.
