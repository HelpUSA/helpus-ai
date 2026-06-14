# HelpUS Watcher Command Protocol

Este documento define como o chat HelpUS deve entender, propor e acompanhar comandos via watcher/AI Bridge Local sem confundir recibos com comandos.

## Objetivo

Tornar o agente capaz de usar o watcher com seguranca operacional, entendendo quando deve apenas interpretar logs, quando deve propor um envelope novo e quando deve parar por risco ou erro de parse.

## Conceitos obrigatorios

O agente deve diferenciar tres coisas:

1. Pedido do usuario: uma instrucao em linguagem natural.
2. Envelope watcher: JSON valido enviado entre marcadores locais.
3. Recibo watcher: resposta como `[AI_LOCAL]`, `[AI_LOCAL_RUN]` ou `[AI_LOCAL_ERRO]`.

Recibos nao sao comandos de entrada. O agente deve analisar o resultado e propor o proximo passo.

## Marcadores locais

Quando precisar enviar um envelope ao watcher, usar marcadores sozinhos nas linhas:

```text
@@AI_BRIDGE_LOCAL_START@@
{ JSON valido aqui }
@@AI_BRIDGE_LOCAL_END@@
```

Nao colocar texto extra na mesma linha dos marcadores.

## Campos minimos do envelope

Um envelope seguro deve conter:

- `command_id`: identificador unico e descritivo.
- `action`: normalmente `run-command`.
- `source_chat_id`: chat de origem.
- `target_chat_id`: destino do watcher.
- `delivery_kind`: normalmente `local_capability`.
- `conversation_id`: frente operacional.
- `from_agent`: quem solicitou.
- `payload.cwd`: diretorio de trabalho.
- `payload.timeout_seconds`: timeout.
- `payload.command`: lista de argumentos do processo.

## Modelo seguro de envelope

```json
{
  "command_id": "helpus_inspect_example_001",
  "action": "run-command",
  "source_chat_id": "CURRENT_CHAT_ID",
  "target_chat_id": "gateway-brain-supervisor",
  "delivery_kind": "local_capability",
  "conversation_id": "helpus_safe_inspection",
  "from_agent": "Wagner supervisor",
  "payload": {
    "cwd": "D:/dev/ai",
    "timeout_seconds": 300,
    "command": [
      "powershell",
      "-NoProfile",
      "-Command",
      "Write-Output 'START'; git status -sb; Write-Output 'END'"
    ]
  }
}
```

## Regras para montar comandos

1. Usar `payload.command` como array JSON, nao como string solta.
2. Usar aspas duplas ASCII no JSON.
3. Evitar aspas curvas, caracteres invisiveis e comandos inline grandes.
4. Para comando grande, preferir script pequeno real ou `python -c` com base64 ASCII.
5. Evitar `$.Name` em PowerShell; usar `$PSItem.Name` ou `$_.Name`.
6. Evitar `python -c` com blocos multiline sem indentacao controlada.
7. Preferir inspecao antes de patch.
8. Nunca misturar dry-run e execucao destrutiva no mesmo comando.
9. Sempre imprimir marcadores de inicio e fim.
10. Sempre validar `git status -sb` no inicio e no fim.

## Como interpretar resultados

### `[AI_LOCAL_RUN] status=acked return_code=0`

Significa que o comando executou com sucesso. O agente deve resumir:
- o que foi feito;
- validacoes que passaram;
- commit/tag se houver;
- estado final do repo;
- proximo micro recomendado.

### `[AI_LOCAL_RUN] status=failed`

Significa que o comando executou e falhou. O agente deve:
- identificar causa provavel;
- dizer se houve alteracao parcial;
- propor comando de inspecao/recuperacao;
- nao repetir o mesmo erro.

### `[AI_LOCAL_ERRO] envelope_parse_error`

Significa que nada foi executado. O agente deve:
- corrigir JSON;
- trocar `$.Name` por `$PSItem.Name` quando aplicavel;
- evitar inline grande;
- reenviar com `command_id` novo;
- se havia delete/move/clean, reenviar primeiro em dry-run/listagem.

## Rotina watcher para cada tarefa

1. Classificar a tarefa: inspecao, patch, validacao, tag ou deploy.
2. Para inspecao: comando somente leitura.
3. Para patch: alterar poucos arquivos e validar.
4. Para validacao: rodar suite real.
5. Para tag: exigir repo limpo.
6. Para deploy: exigir autorizacao explicita.
7. Em erro: parar, resumir e propor recuperacao.

## Comandos reais de validacao do repo

```powershell
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check
```

## Comandos destrutivos ou sensiveis

Exigem dry-run, explicacao e autorizacao explicita:

- `git reset --hard`
- `git clean -fd` ou `git clean -fdx`
- `git push --force`
- remocoes em massa
- migracoes destrutivas de banco
- alteracao de secrets
- deploy

## Como propor proximos passos

O agente deve propor proximos micros pequenos, por exemplo:

- Micro A: inspecionar estado.
- Micro B: aplicar patch minimo.
- Micro C: validar e commit.
- Micro D: criar tag segura.

Cada micro deve ter objetivo, arquivos provaveis, risco, validacoes e criterio de pronto.

## Criterio de pronto

O chat entende o watcher quando consegue:

- nao confundir recibos com comandos;
- corrigir envelope parse error;
- montar JSON estrito;
- escolher comandos seguros;
- validar com a suite real;
- parar quando houver risco;
- relatar resultado final com proximo passo.

## Relacao com provedor local de IA

O provedor local de IA pode ajudar a interpretar contexto, recibos e erros, mas nao deve executar comandos.

Fluxo correto:

1. Provedor local ou contexto operacional ajuda a analisar.
2. watcher_intent classifica a tarefa.
3. watcher_envelope_builder gera envelope JSON seguro.
4. watcher / AI Bridge Local executa.
5. smokes, build e git diff --check validam.
6. chat resume o resultado e recomenda o proximo micro.

Componentes planejados relacionados:

- operational_context
- local_ai_provider
- watcher_intent
- watcher_envelope_builder
- watcher_recovery
