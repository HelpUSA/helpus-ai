# Relatório de Restauração de Produção e Autenticação Google — HelpUS AI

> **Data:** 07 de Outubro de 2026  
> **Responsável Técnico:** Equipe HelpUS / Antigravity AI  
> **Domínio de Produção:** [https://ai.helpusbr.com](https://ai.helpusbr.com)  
> **API Railway:** [https://helpus-api-production.up.railway.app](https://helpus-api-production.up.railway.app)  
> **Repositório GitHub:** `https://github.com/HelpUSA/helpus-ai.git` (Branch: `main`)  

---

## 1. Contexto e Motivação do Chamado

O assistente inteligente HelpUS AI (`ai.helpusbr.com`) apresentava tela de indisponibilidade com o erro `404 DEPLOYMENT_NOT_FOUND` emitido pelo nó Edge da Vercel (`gru1`). Adicionalmente, identificou-se que o backend no Railway estava inativo e, após o restabelecimento do serviço, o fluxo de login via Google Identity Services (GIS) não abria a solicitação de conta para o usuário.

---

## 2. Diagnóstico Técnico

### 2.1 Indisponibilidade de Produção (Railway + Vercel)
* **Vercel:** O domínio `ai.helpusbr.com` apontava corretamente no DNS para a Vercel, porém o projeto na conta Vercel (`helpusecommerce-7210`) estava desvinculado/sem deployment ativo, gerando o erro de roteamento `404`.
* **Railway:** O serviço anterior `helpus-api-production.up.railway.app` retornava `404 Application not found` e o projeto não constava mais na lista ativa da conta Railway (`helpusa`).

### 2.2 Falha no Fluxo de Login Google
* **Google One Tap (`prompt`):** O frontend dependia exclusivamente da chamada `window.google.accounts.id.prompt()`. O método One Tap sofre supressões silenciosas automáticas do Google em casos de:
  1. *Exponential Cooldown:* quando o usuário fecha o balão uma vez, novas aberturas são bloqueadas por 2 horas a 1 semana;
  2. Modos de navegação privada ou bloqueio de cookies de terceiros;
  3. Ausência da URL `https://ai.helpusbr.com` nas *Authorized JavaScript origins* do Google Cloud Console.
* **Botão Nativo Oculto:** O botão padrão do Google (`renderButton`) estava renderizado dentro de uma `div id="google-login-button" className="hidden"`. Ao falhar o One Tap, nenhum botão alternativo ficava visível para o usuário clicar.

---

## 3. Ações Executadas e Soluções Implementadas

### 3.1 Restauração da Infraestrutura Railway
1. **Projeto e Banco:** Criado novo projeto `helpus-ai` (`86bff38c-ee1a-4117-9f24-75d1c46639ba`) e provisionado banco gerenciado **PostgreSQL** (`21999b21-3eee-499c-89b8-987578a18489`).
2. **Serviço Backend (`helpus-api`):** Conectado diretamente ao repositório GitHub `HelpUSA/helpus-ai` (branch `main`).
3. **Configuração de Ambiente:**
   * `ENVIRONMENT=production`
   * `AI_PROVIDER=gemini`
   * `GEMINI_MODEL=gemini-2.5-flash-lite`
   * `DATABASE_URL=${{Postgres.DATABASE_URL}}` (rede privada `postgres.railway.internal:5432`)
   * `CORS_ORIGINS=https://ai.helpusbr.com,https://helpus-ai.vercel.app,http://localhost:3000`
4. **Domínio e Rede:** Gerado domínio público `https://helpus-api-production.up.railway.app` e target port alinhado para a porta 8080.
5. **Resultado:** Backend online (`/saude` e `/status` respondendo HTTP 200 OK) e tabelas criadas automaticamente na inicialização.

### 3.2 Restauração do Frontend na Vercel
1. Projeto `ai` vinculado à organização `help-us` e conectado ao repositório GitHub.
2. Variáveis de produção configuradas:
   * `NEXT_PUBLIC_API_URL=https://helpus-api-production.up.railway.app`
   * `NEXT_PUBLIC_GOOGLE_CLIENT_ID=812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com`
3. Domínio `ai.helpusbr.com` associado e validado.
4. Deploy de produção gerado com sucesso via `vercel deploy --prod --yes`.

### 3.3 Aprimoramento da Autenticação Google (GIS)
* **Arquivo alterado:** `frontend/src/app/page.tsx`
  1. **Fallback do Client ID:** Definido fallback seguro em código para evitar valor indefinido.
  2. **Renderização de Botões Oficiais Visíveis (`renderizarBotoesGoogle`):**
     * `google-login-button-main`: card destacado no centro do chat quando o usuário não estiver logado.
     * `google-login-button-header`: no menu suspenso de ações superiores.
     * `google-login-button-sidebar`: no rodapé da barra lateral de conversas.
  3. **Disparador Inteligente (`dispararLoginGoogle`):** Aciona o botão oficial via clique no elemento interno gerado pelo Google ou reinicializa o prompt com tratamento de erros.
  4. **Desconexão Completa no Logout (`sair`):** Adicionada chamada a `window.google?.accounts?.id?.disableAutoSelect()`, forçando o Google a esquecer a auto-seleção e pedir a conta no próximo login.
  5. **Card Central no Chat Vazio:** Quando não autenticado, um card elegante orienta o usuário a se identificar antes de iniciar a conversa.

---

## 4. Recursos e Endpoints Recentes no Core AI

| Módulo / Recurso | Tipo | Descrição |
| :--- | :--- | :--- |
| **Streaming SSE** | Backend / Frontend | `/chat/stream` com digitação em tempo real estilo ChatGPT. |
| **Voz em Tempo Real** | Frontend | Web Speech API integrada com reconhecimento e síntese de voz no modal de chamada. |
| **Visão Multimodal** | Backend / Frontend | Envio e análise de fotos e documentos com LLM. |
| **Transbordo Humano CRM** | Backend Admin | Endpoints `/admin/atendimentos`, `/admin/handoff` e `/admin/responder`. |
| **Agendamento Google Calendar** | Backend / Ferramentas | Endpoint `/agendar` para criação de eventos e download de arquivos `.ics`. |
| **Proposta Comercial** | Backend / Ferramentas | Endpoint `/gerar-proposta` para emissão automática de propostas em HTML/SVG prontas para PDF. |

---

## 5. Verificações de Qualidade e Conformidade

* Compilação Next.js (`npm run build`): Concluída com sucesso em 3.8s sem erros de tipagem.
* Compilação Python (`py_compile`): Todos os módulos backend compilaram sem erros de sintaxe.
* Teste HTTP de Produção: `curl -I https://ai.helpusbr.com` retornou `HTTP/1.1 200 OK`.
* Transparência de Chaves: A chave `GEMINI_API_KEY` deve ser mantida nas variáveis de ambiente do Railway para habilitar o processamento LLM.
