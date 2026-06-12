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
