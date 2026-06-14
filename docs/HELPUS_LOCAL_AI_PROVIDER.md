# HelpUS Local AI Provider

## Objetivo

Documentar a frente de provedor local/offline de IA para tornar o HelpUS mais independente, privado e resiliente quando houver falha ou indisponibilidade de provedores externos.

## Ideia central

O HelpUS pode usar um runtime local de IA, como LM Studio, Ollama ou outro servidor compativel com API local, para tarefas operacionais que nao exigem internet.

Essa camada nao substitui o watcher. O watcher continua sendo o mecanismo seguro de execucao local. O provedor local ajuda o chat a pensar, resumir documentos, interpretar recibos, classificar intencoes e propor proximos micros com mais privacidade.

## Beneficios esperados

- Reduzir dependencia de internet para analise operacional.
- Evitar envio de docs, logs e arquivos sensiveis para provedores externos quando nao for necessario.
- Permitir modo degradado/offline para leitura de docs, resumo de estado e classificacao de intencoes watcher.
- Usar os protocolos operacionais como prompt/contexto local.
- Manter fallback para provedores externos quando configurado e autorizado.

## Limites importantes

- O provedor local nao deve executar comandos diretamente.
- Execucao continua passando pelo watcher / AI Bridge Local.
- O modelo local pode errar; portanto toda acao deve continuar validada por smokes, build e git diff --check.
- Se o runtime local estiver indisponivel, a aplicacao nao deve quebrar.
- Nenhum segredo deve ser impresso em logs ou enviado a modelos externos sem autorizacao.

## Micro 29 - Provedor local/offline de IA

Arquivos provaveis:

- backend/local_ai_provider.py
- backend/operational_context.py
- scripts/watcher/smoke_local_ai_provider.py
- docs/HELPUS_LOCAL_AI_PROVIDER.md

Criterio de pronto:

- smoke valida configuracao local sem exigir internet;
- app nao quebra se o provedor local estiver indisponivel;
- fallback atual continua funcionando;
- nenhum segredo e exposto;
- suite operacional passa;
- health report passa;
- build frontend passa;
- git diff --check passa.

## Uso operacional esperado

Quando o usuario pedir continuidade, analise de docs, resumo de estado ou interpretacao de recibos watcher, o HelpUS deve consultar primeiro o contexto operacional local. Se houver runtime local disponivel, ele pode ser usado para apoio analitico.

Quando a tarefa envolver execucao, patch, commit, tag, deploy ou alteracao sensivel, o HelpUS deve continuar usando o fluxo seguro: contexto operacional, classificacao de intencao, builder de envelope, watcher, validacao real e resumo do resultado.

## Configuracao futura sugerida

Variaveis provaveis:

- HELPUS_LOCAL_AI_ENABLED=false
- HELPUS_LOCAL_AI_BASE_URL=http://localhost:1234/v1
- HELPUS_LOCAL_AI_MODEL=local-model
- HELPUS_LOCAL_AI_TIMEOUT_SECONDS=60

A configuracao deve ser opcional e segura por padrao.
