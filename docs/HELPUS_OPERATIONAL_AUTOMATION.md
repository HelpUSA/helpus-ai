# HelpUS AI - Automacao operacional

## Estado atual

A frente operacional da HelpUS AI possui validacoes automatizadas para reduzir comandos quebrados, erros de envelope watcher e regressao em memorias/projetos.

## Validacoes implementadas

1. Intent layer e command builder: validam send_chat e run_command antes do envio.
2. Behavior smoke: cobre contrato operacional do prompt, builder e preflight.
3. Watcher error classifier: classifica falhas parse, semantic, delivery, timeout e unknown.
4. Telemetria local: registra eventos JSONL simples para diagnostico.
5. Command safety: detecta comandos destrutivos e exige dry-run ou autorizacao explicita.
6. Watcher stress smoke: exercita envelopes validos e invalidos em volume.
7. Memory panel contract smoke: protege marcadores essenciais do painel de memorias.

## Suite recomendada

powershell
python -m py_compile backend/main.py backend/banco.py backend/cerebro.py backend/command_builder.py backend/preflight_validator.py backend/intent_layer.py backend/watcher_errors.py backend/telemetry.py backend/command_safety.py scripts/watcher/smoke_behavior_ai.py scripts/watcher/smoke_intent_layer.py scripts/watcher/smoke_watcher_errors.py scripts/watcher/smoke_telemetry.py scripts/watcher/smoke_command_safety.py scripts/watcher/smoke_watcher_stress.py scripts/watcher/smoke_memory_panel_contract.py
python scripts/watcher/smoke_behavior_ai.py
python scripts/watcher/smoke_intent_layer.py
python scripts/watcher/smoke_watcher_errors.py
python scripts/watcher/smoke_telemetry.py
python scripts/watcher/smoke_command_safety.py
python scripts/watcher/smoke_watcher_stress.py
python scripts/watcher/smoke_memory_panel_contract.py
npm --prefix frontend run build
git diff --check


## Proximas frentes

- Integrar telemetria ao painel admin.
- Criar smoke unico de release operacional.
- Criar relatorio de saude local com ultimos commits, status, build e smokes.
- Evoluir painel de memorias com busca, tags e historico de alteracoes.
- Preparar tag de release apenas apos suite completa verde.

## Release smoke e health report

A suite operacional agora tambem possui dois utilitarios de fechamento:

- scripts/watcher/smoke_operational_release.py: executa a suite operacional principal em uma chamada unica.
- scripts/watcher/health_report.py: gera reports/helpus_health_report.json com status git, HEAD, log recente e existencia dos smokes.
- scripts/watcher/smoke_health_report.py: valida a geracao e o contrato minimo do health report.

## Comando final recomendado antes de tag

powershell
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check
git status -sb


## Criterio para tag operacional

Criar tag somente quando release smoke, health report, build frontend e diff check estiverem verdes com repo limpo/alinhado.

## Baseline admin telemetry UI - 2026-06-13

Ponto seguro criado apos integrar telemetria operacional ao painel admin.

- Tag: helpus-admin-telemetry-ui-2026-06-13
- Commit: eebdc82 Add admin telemetry card to operational panel
- Backend: GET /admin/telemetry protegido por obter_admin_google e baseado em summarize_events.
- Frontend: /admin exibe o card Telemetria operacional usando /admin/telemetry.
- Smokes adicionados: smoke_admin_telemetry_route_contract.py e smoke_admin_telemetry_ui_contract.py.
- Suite agregada: smoke_operational_release.py inclui os contratos de rota e UI.
- Health report: health_report.py lista os smokes de telemetria admin.

### Validacao obrigatoria antes de novas alteracoes

Executar, nesta ordem:

powershell
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check


### Criterio de continuidade

Prosseguir apenas se a suite operacional, health report, build frontend e diff check estiverem verdes. Se houver alteracoes locais inesperadas, parar e inspecionar antes de aplicar qualquer patch.

### Proximas frentes recomendadas

1. Inspecao visual/manual do painel /admin em ambiente local ou producao.
2. Melhorar o resumo de telemetria com ultimos eventos, ultima falha e timestamp mais recente.
3. Adicionar smoke de contrato para novos campos antes de expor na UI.
4. Manter commits pequenos, com uma frente por vez e sem deploy automatico.
