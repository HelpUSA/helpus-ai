# HelpUS AI - Roadmap

## Prioridade 1 - Renderizacao de respostas

Melhorar a forma como as respostas aparecem no chat. Hoje o texto e exibido de forma simples. A proxima evolucao deve suportar Markdown com melhor visual para titulos, listas, links e blocos de codigo.

Tarefas:

- Suporte visual a Markdown.
- Blocos de codigo com fonte monoespacada.
- Links clicaveis em respostas.
- Listas numeradas e bullets com espacamento melhor.
- Fontes consultadas menos intrusivas.

## Prioridade 2 - UX do botao Copiar

O botao Copiar ja existe nas respostas. A melhoria recomendada e exibir feedback visual ao usuario.

Tarefas:

- Mostrar texto Copiado por alguns segundos.
- Tratar navegadores sem navigator.clipboard.
- Evitar erro silencioso ao copiar.

## Prioridade 3 - Mobile

A interface foi refinada para se aproximar de um chat moderno, mas ainda precisa de teste manual em celulares reais.

Tarefas:

- Testar em iPhone e Android.
- Fechar sidebar automaticamente ao selecionar conversa.
- Verificar comportamento do teclado virtual.
- Garantir que o composer nao fique coberto.
- Validar login Google em mobile.

## Prioridade 4 - Admin

O painel /admin deve seguir o mesmo padrao visual do chat.

Tarefas:

- Cards modernos de status.
- Exibir status da API, modelo, auth, banco e ambiente.
- Exibir versao ou commit atual.
- Exibir links de producao e comandos uteis.

## Prioridade 5 - Observabilidade

Adicionar visibilidade operacional para deploys e diagnostico.

Tarefas:

- Endpoint de versao.
- Commit atual em status/admin.
- Horario do ultimo deploy.
- Logs estruturados para erros de IA, auth e banco.

## Prioridade 6 - Testes

O smoke test existe e valida disponibilidade basica. A proxima fase deve ampliar cobertura.

Tarefas:

- Testes unitarios backend.
- Testes de API.
- Testes frontend/componentes.
- Smoke local.
- Teste e2e basico para login mockado e chat.

## Prioridade 7 - Historico

Melhorar a experiencia das conversas salvas.

Tarefas:

- Gerar titulos automaticos melhores.
- Ordenar por ultima atividade.
- Exibir data curta.
- Melhorar confirmacao antes de apagar.
