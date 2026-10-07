<!-- HELPUS_DOCS_CLOUD_INDEX_START -->

# Documentação HelpUS AI

## Estado atual (Outubro / 2026)

- Produção restaurada e ativa no domínio [https://ai.helpusbr.com](https://ai.helpusbr.com).
- Frontend hospedado na Vercel (Next.js 16 + Turbopack + React 19).
- Backend containerizado ativo no Railway (`https://helpus-api-production.up.railway.app`).
- Banco gerenciado PostgreSQL provisionado e conectado na rede privada do Railway.
- Autenticação Google Identity Services (GIS) aprimorada com botões oficiais nativos e suporte a `disableAutoSelect`.
- Recursos recentes: Streaming SSE, Chamada de Voz em tempo real, Visão Multimodal, Transbordo Humano CRM, Agendamento Google Calendar e Propostas Comerciais em PDF.

## Documentos principais

- [Relatório de Restauração de Produção & Google Auth (07/10/2026)](HELPUSAI_PRODUCTION_RESTORATION_AND_AUTH_REPORT_2026-10-07.md)
- [Roadmap Estratégico & Arquitetura Multissoluções](HELPUSAI_STRATEGIC_ARCHITECTURE_ROADMAP.md)
- [Documento Mestre Unificado](HELPUS_PROJECT_MASTER.md)
- [Arquitetura de produção](ai/HELPUS_PRODUCTION_ARCHITECTURE.md)
- [Implantação Railway](ai/HELPUS_RAILWAY_MULTI_AI_DEPLOYMENT.md)
- [Runbook de Produção](ai/HELPUS_PRODUCTION_RUNBOOK.md)
- [Checklist de Produção](ai/HELPUS_PRODUCTION_CHECKLIST.md)
- [Plano de auditoria cloud](ai/HELPUS_CLOUD_INFRA_AUDIT_PLAN.md)
- [Integração runtime multi-IA](ai/HELPUS_RUNTIME_MULTI_AI_INTEGRATION.md)
- [Auditoria documental](ai/HELPUS_DOCS_AUDIT_2026-07-20.md)
- [Rollout Obsidian](obsidian/HELPUSAI_PRODUCTION_ROLLOUT.md)

A produção é executada de forma desacoplada entre a Vercel (frontend) e o Railway (backend + PostgreSQL). O computador local é utilizado exclusivamente para desenvolvimento, auditorias e testes.

<!-- HELPUS_DOCS_CLOUD_INDEX_END -->
