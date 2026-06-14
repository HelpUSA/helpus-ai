# HelpUS Chat Watcher Intelligence Roadmap

## Objetivo

Tornar o chat HelpUS mais inteligente, independente e seguro ao interpretar, propor e acompanhar comandos via watcher / AI Bridge Local.

## Estado atual seguro

- Repo principal: D:/dev/ai
- Branch: main
- Remoto: origin/main
- Protocolos existentes: HELPUS_AGENT_OPERATING_PROTOCOL.md, HELPUS_WATCHER_COMMAND_PROTOCOL.md e HELPUS_OPERATIONAL_AUTOMATION.md.
- Smokes existentes: smoke_operational_release.py, smoke_health_report.py, smoke_agent_operating_protocol.py e smoke_watcher_command_protocol.py.

## Problema que falta resolver

Os documentos e smokes existem, mas o chat ainda precisa de uma camada explicita de inteligencia operacional para consultar esses protocolos antes de responder pedidos como prossiga, continue, use o watcher, corrija e reenvie, o comando falhou, quais as proximas atividades e deixe o chat independente.

Sem essa camada, o chat pode depender demais do historico da conversa e pode voltar a confundir recibos do watcher com comandos de entrada.

## Ordem recomendada para comecar

### Micro 24 - Contexto operacional do agente

Criar modulo backend que carregue os docs operacionais e entregue um resumo seguro para o chat.

Arquivos provaveis:
- backend/operational_context.py
- scripts/watcher/smoke_operational_context.py
- scripts/watcher/smoke_operational_release.py
- scripts/watcher/health_report.py

Criterio de pronto: modulo carrega docs obrigatorios, smoke confirma marcadores essenciais, suite operacional passa, health report passa, build frontend passa e git diff --check passa.

### Micro 25 - Intencao watcher

Criar classificador simples para entender pedidos relacionados ao watcher.

Categorias minimas: inspect, patch, validate, commit, tag, recover e stop.

Arquivos provaveis:
- backend/watcher_intent.py
- scripts/watcher/smoke_watcher_intent.py

Criterio de pronto: smoke cobre frases reais do operador, nao trata AI_LOCAL_RUN ou AI_LOCAL_ERRO como comando novo e sabe quando resumir resultado ou propor envelope novo.

### Micro 26 - Builder seguro de envelopes watcher

Criar gerador de envelopes watcher com JSON estrito e regras de seguranca.

Regras obrigatorias: command_id novo, payload.cwd explicito, payload.command como array, marcadores locais sozinhos nas linhas, evitar inline grande e nunca repetir o mesmo envelope apos envelope_parse_error.

Arquivos provaveis:
- backend/watcher_envelope_builder.py
- scripts/watcher/smoke_watcher_envelope_builder.py

### Micro 27 - Recuperacao de erros watcher

Criar rotina para interpretar falhas e propor recuperacao segura.

Entradas: envelope_parse_error, return_code diferente de zero, erro de build, erro de smoke, erro de git diff --check, arquivo inesperado modificado e repo sujo antes de patch.

Arquivos provaveis:
- backend/watcher_recovery.py
- scripts/watcher/smoke_watcher_recovery.py

### Micro 28 - Integracao com resposta do chat

Integrar contexto operacional, intencao watcher, builder e recuperacao no fluxo real de resposta.

Objetivo: quando o usuario disser prossiga ou continue, o chat consulta contexto, escolhe micro seguro e propoe comando watcher valido. Quando receber recibo, resume resultado e escolhe proximo passo. Quando receber erro, corrige sem repetir o erro. Quando houver risco, para e pede autorizacao.

## Validacoes obrigatorias antes de cada commit

Executar sempre:
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check

## Regras de seguranca

- Nao fazer deploy sem autorizacao explicita.
- Nao usar git reset --hard, git clean, remocoes em massa, migracoes destrutivas ou alteracao de secrets sem dry-run e autorizacao.
- Nao commitar se houver arquivo inesperado modificado.
- Nao criar tag se o repo nao estiver limpo.
- Em erro de parse de envelope, considerar que nada foi executado e gerar command_id novo.
- Em falha parcial, inspecionar antes de corrigir.

## Criterio de independencia do chat

O chat sera considerado mais independente quando conseguir consultar docs operacionais automaticamente, identificar a tarefa correta sem depender de historico manual longo, diferenciar recibo erro e pedido novo, propor envelopes JSON validos, corrigir erro de parse sem repetir o erro, validar com suite real, resumir resultado e recomendar o proximo micro.

### Micro 29 - Provedor local/offline de IA

Adicionar suporte opcional a um runtime local de IA, como LM Studio ou outro servidor compativel com API local, para apoiar raciocinio operacional privado e modo offline/degradado.

Objetivo:

- consultar docs e protocolos operacionais localmente;
- resumir estado do repo sem depender de provedor externo;
- classificar intencoes watcher com mais privacidade;
- interpretar recibos e erros sem enviar logs sensiveis para fora;
- manter execucao real sempre via watcher;
- manter fallback para provedores externos quando configurado.

Arquivos provaveis:

- backend/local_ai_provider.py
- backend/operational_context.py
- scripts/watcher/smoke_local_ai_provider.py
- docs/HELPUS_LOCAL_AI_PROVIDER.md

Criterio de pronto: runtime local opcional, falha segura quando indisponivel, nenhum segredo exposto, smokes verdes, health report verde, build frontend verde e git diff --check verde.
