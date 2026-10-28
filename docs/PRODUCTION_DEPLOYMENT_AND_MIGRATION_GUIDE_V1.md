# Guia de Deploy em Produção e Homologação de Banco de Dados — IAHelpUS v1

**Data**: Outubro / 2026  
**Repositório**: `https://github.com/HelpUSA/helpus-ai.git`  
**Branch de Homologação**: `feature/ui-ux-modernization-v1`  
**Alvo de Produção**: `https://ai.helpusbr.com/` (Vercel Serverless + Railway / Supabase Postgres)  

---

## 1. Inventário de Variáveis de Ambiente (Vercel & Railway)

Para eliminar o fallback estático e habilitar a persistência em nuvem com isolamento rigoroso, as seguintes variáveis devem ser configuradas nas variáveis de ambiente da Vercel (Production & Preview) e do Railway Backend:

| Variável | Tipo / Formato | Descrição & Finalidade | Política de Segurança |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | String Secreta (`AIzaSy...`) | Chave oficial Google AI Studio / Vertex AI para os modelos Gemini 2.5 Flash, 2.5 Flash-Lite e 2.5 Pro. | Segredo crítico. Nunca comitar no Git. |
| `DATABASE_URL` | URI (`postgresql://...`) | Conexão com pool de conexões do PostgreSQL gerenciado (Neon / Railway / Supabase). | Segredo crítico. Uso restrito a server-side. |
| `ADMIN_EMAILS` | Lista CSV (`email1,email2`) | E-mails autorizados para acesso ao painel `/admin` e rotas administrativas (fail-closed). | Se vazio, todo acesso a `/admin` é bloqueado com HTTP 403. |
| `AUTH_REQUIRED` | Boolean (`true` / `false`) | Exigência de login Google OAuth para uso do chat. | `true` em produção corporativa; `false` em modo teste público. |
| `HELPUS_BRIDGE_API_TOKEN` | Token Bearer (64 hex chars) | Chave secreta dedicada para autorização de comandos da ponte de agentes. | Validado via `test_bridge_auth_unit.py`. |
| `CORS_ORIGINS` | Lista CSV de URLs | Origens permitidas para requisições cross-origin no FastAPI. | `https://ai.helpusbr.com,https://helpus-ai.vercel.app` |
| `NEXT_PUBLIC_API_URL` | URL Pública | Endpoint backend consumido pelo frontend Next.js. | Vazio em Vercel (`/api` rewrite) ou URL do Railway. |
| `DEEPSEEK_API_KEY` | String Secreta (Opcional) | Chave de fallback para DeepSeek Chat e DeepSeek R1 Reasoner. | Provedor secundário configurado em `multi_ai_provider.py`. |
| `OPENAI_API_KEY` | String Secreta (Opcional) | Chave de fallback para modelos GPT-4o e GPT-4o-mini. | Provedor secundário configurado em `cerebro.py`. |

---

## 2. Procedimento de Aplicação da Migração SQL `002`

O script [`migrations/002_tenant_isolation_and_indexes.sql`](../migrations/002_tenant_isolation_and_indexes.sql) adiciona índices compostos essenciais para busca e isolamento de inquilinos em $O(\log N)$:

### 2.1 Pré-Requisitos e Salvaguardas
1. **Backup Snapshot**: Executar dump completo antes da execução:
   ```bash
   pg_dump -d "$DATABASE_URL" -Fc -f "backup_pre_migration_002_$(date +%Y%m%d_%H%M%S).dump"
   ```
2. **Homologação em Staging**: O script deve ser aplicado no banco de dados de *staging* antes de qualquer execução em produção.

### 2.2 Índices Adicionados
```sql
CREATE INDEX IF NOT EXISTS idx_conversas_tenant_session
ON conversas (LOWER(user_email), session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversas_tenant_project
ON conversas (LOWER(user_email), project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_projetos_tenant_created
ON projetos (LOWER(user_email), created_at ASC);
```

### 2.3 Verificação de Performance (EXPLAIN ANALYZE)
Após aplicar o script, validar que o planejador de queries do PostgreSQL utiliza os novos índices:
```sql
EXPLAIN ANALYZE
SELECT session_id, MAX(created_at)
FROM conversas
WHERE LOWER(user_email) = 'usuario@helpusbr.com'
GROUP BY session_id
ORDER BY MAX(created_at) DESC
LIMIT 50;
-- Deve exibir: Index Scan using idx_conversas_tenant_session (Cost < 10ms)
```

### 2.4 DDL de Rollback Reversível
Caso seja necessária a reversão imediata:
```sql
DROP INDEX IF EXISTS idx_conversas_tenant_session;
DROP INDEX IF EXISTS idx_conversas_tenant_project;
DROP INDEX IF EXISTS idx_projetos_tenant_created;
```

---

## 3. Protocolo de Merge e Verificação Pós-Deploy

1. **Testes Unitários & Estáticos**: Executar `python -m unittest discover -s tests -v` (requisito: 35/35 testes verdes).
2. **Build de Produção**: Executar `npm --prefix frontend run build` (requisito: 0 erros TypeScript, rotas prerenderizadas).
3. **Smoke Test Pós-Deploy**:
   - `GET /status`: Deve retornar `{"status": "online", "modelo_carregado": true}`.
   - `GET /modelos`: Deve retornar a lista oficial dos 5 modelos e `default_model: "gemini-2.5-flash"`.
   - `POST /chat`: Enviar mensagem teste e validar que `provider_used` não é `"fallback"`.
   - `GET /conversas`: Validar que conversas de outros usuários não aparecem.
