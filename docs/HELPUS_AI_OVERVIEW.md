# HelpUS AI - Visao Geral

## O que e a aplicacao

O HelpUS AI e uma aplicacao web de assistente por chat. O sistema oferece login com Google, historico de conversas por usuario, respostas de IA via Gemini, busca web com fontes, consulta de clima e painel administrativo de status.

A aplicacao esta publicada em producao com frontend na Vercel e backend na Railway. O dominio principal do usuario e https://ai.helpusbr.com.

## Objetivo do produto

O objetivo e entregar um assistente simples, seguro e facil de usar, com experiencia visual proxima a um chat moderno. O foco atual e estabilizar a base tecnica, melhorar a interface e manter um fluxo de deploy validado por smoke test.

## Componentes principais

- Frontend: Next.js, React, TypeScript e Tailwind CSS.
- Backend: Python, FastAPI e Uvicorn.
- IA: Gemini.
- Autenticacao: Google OAuth.
- Banco: Railway PostgreSQL.
- Deploy frontend: Vercel.
- Deploy backend: Railway.
- Smoke test: npm run smoke:prod.

## URLs de producao

- Frontend: https://ai.helpusbr.com
- Backend: https://helpus-api-production.up.railway.app
- Admin: https://ai.helpusbr.com/admin

## Recursos implementados

- Chat principal com composer no rodape.
- Envio por Enter e quebra de linha com Shift+Enter.
- Bloqueio do chat quando nao ha login.
- Login com Google.
- Historico por usuario autenticado.
- Criar nova conversa.
- Carregar conversas anteriores.
- Apagar conversas.
- Botao Copiar nas respostas.
- Busca web com exibicao de fontes.
- Consulta de clima com normalizacao de cidades brasileiras.
- Painel /admin.
- Endpoints /saude e /status.
- Smoke test automatizado.

## Status atual

A aplicacao esta funcional em producao. As ultimas rodadas focaram em aproximar o layout do estilo ChatGPT: sidebar escura, header mais compacto, composer arredondado com botao circular, estado inicial com cards de sugestao e mensagens mais limpas.
