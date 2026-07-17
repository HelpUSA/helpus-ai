# HelpUSAI — Status do planejamento de conhecimento e memória

Data: 2026-07-17
Repositório: `D:/dev/ai`
Remoto: `HelpUSA/helpus-ai`

## Decisão

Conhecimento persistente, memória do usuário, memória de projeto, continuidade
das conversas, recuperação documental e conhecimento operacional do Watcher
serão implementados dentro do AI HelpUS.

`ai-bridge-local` permanece uma aplicação externa e não será alterada por este
programa.

## Motivo

Um teste real entre chats mostrou que o agente conhecia conceitualmente o
protocolo, mas recusou uma execução segura por acreditar que uma IA dentro do
chat não poderia usar o Watcher.

A correção planejada pertence ao bootstrap permanente e aos testes de regressão
do AI HelpUS.

## Documento canônico

`docs/ai/HELPUS_KNOWLEDGE_MEMORY_ARCHITECTURE_PLAN.md`

## Sequência aprovada

1. KM-1 — bootstrap operacional permanente;
2. KM-2 — domínio e API de memória;
3. KM-3 — continuidade das conversas;
4. KM-4 — ingestão de conhecimento;
5. KM-5 — recuperação híbrida;
6. KM-6 — context builder;
7. KM-7 — interface administrativa;
8. KM-8 — avaliação e produção.

## Estado atual

Este checkpoint registra somente planejamento.

Nenhuma migration, alteração de prompt ativo, ativação de embedding ou
alteração em `ai-bridge-local` é realizada por esta documentação.
