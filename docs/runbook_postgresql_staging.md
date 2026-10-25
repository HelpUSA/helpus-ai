# HelpUS AI — Runbook de Homologação e Migração PostgreSQL (Staging)

> **Status Atual de Execução Remota**: `BLOCKED` (Aguardando liberação de credenciais seguras e isoladas pelo Master SuperAdmin).  
> **Escopo**: Banco de dados relacional PostgreSQL do ambiente de Staging. Nenhuma execução direta em Produção é permitida nesta etapa.

---

## 1. Princípios e Invariantes de Segurança
1. **Fencing Estrito de Ambiente**: Certificar-se de que a variável `DATABASE_URL` aponte exclusivamente para a instância isolada de **Staging** (ex: `staging-db.helpusbr.com`).
2. **Zero Segredos**: Jamais expor segredos, tokens de serviço ou strings de conexão no código-fonte, branches públicas ou issues do GitHub.
3. **Branch de Homologação**: Confirmar que a branch ativa seja `feature/ui-ux-modernization-v1`.
4. **Alinhamento de Schema e DDL**: Todos os campos de carimbo temporal utilizam `TIMESTAMPTZ` (Timestamp with time zone), índices com normalização `LOWER(user_email)` e chaves primárias alinhadas rigorosamente com `backend/banco.py`.
5. **Remoção de Migração Automática no Startup**: Nenhuma migração DDL ou backfill de dados é executado na inicialização da aplicação FastAPI. Todas as alterações são estritamente versionadas e registradas na tabela `schema_migrations`.
6. **Não-Eleição Silenciosa de Posse**: Sessoes legadas com mais de um usuário associado no histórico jamais têm um proprietário escolhido arbitrariamente por `ON CONFLICT DO NOTHING`. Conflitos são diagnosticados e isolados para decisão auditada.

---

## 2. Procedimento de Backup Físico/Lógico Pré-Migração
Antes de aplicar qualquer migração DDL em staging, execute o backup físico/lógico completo:

```bash
# 1. Definir carimbo de data/hora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_helpus_staging_pre_mig003_${TIMESTAMP}.dump"

# 2. Executar dump custom format (compactado e transacional)
pg_dump -Fc -v -d "${DATABASE_URL}" -f "${BACKUP_FILE}"

# 3. Validar integridade e tamanho do arquivo gerado
ls -lh "${BACKUP_FILE}"
pg_restore -l "${BACKUP_FILE}" | head -n 30
```

---

## 3. Teste Obrigatório de Restauração em Sandbox
Valide o backup gerado restaurando-o em um schema ou banco temporário de teste para comprovar a recuperabilidade total dos dados antes de qualquer alteração no banco real de staging:

```bash
# 1. Criar banco efêmero de verificação
createdb -h localhost -U postgres helpus_staging_verify_temp

# 2. Restaurar backup para teste
pg_restore --clean --if-exists -d helpus_staging_verify_temp "${BACKUP_FILE}"

# 3. Executar contagem de verificação
psql -d helpus_staging_verify_temp -c "SELECT COUNT(*) FROM conversas;"

# 4. Limpeza do banco de teste após validação bem-sucedida
dropdb -h localhost -U postgres helpus_staging_verify_temp
```

---

## 4. Diagnóstico Read-Only Pré-Migração (Detecção de Conflitos)
Antes de inserir dados na tabela `sessoes`, execute o script de diagnóstico para quantificar sessões limpas e sessões confluentes:

```bash
# Executa diagnóstico read-only
python migrations/reconcile_sessoes_diagnostic.py
```

Ou execute diretamente via SQL:
```sql
SELECT session_id, COUNT(DISTINCT LOWER(user_email)) AS distinct_owners,
       ARRAY_AGG(DISTINCT LOWER(user_email)) AS conflicting_emails,
       COUNT(*) AS message_count,
       MIN(created_at) AS first_seen, MAX(created_at) AS last_seen
FROM conversas
WHERE session_id IS NOT NULL AND session_id != ''
GROUP BY session_id
HAVING COUNT(DISTINCT LOWER(user_email)) > 1
ORDER BY message_count DESC;
```

---

## 5. Aplicação da Migration 003 (`migrations/003_sessoes_schema_and_diagnostic.sql`)
Aplica a criação da tabela autoritativa `sessoes`, da trilha de auditoria `admin_audit_events` e reconcilia apenas as sessões legadas não-confluentes:

```bash
psql -d "${DATABASE_URL}" -f migrations/003_sessoes_schema_and_diagnostic.sql
```

Estrutura aplicada:
- Tabela `schema_migrations`: Versionamento formal de banco.
- Tabela `sessoes`: `session_id VARCHAR(120) PRIMARY KEY`, `user_email VARCHAR(255)`, `project_id VARCHAR(100) DEFAULT 'general'`, `created_at TIMESTAMPTZ`, `updated_at TIMESTAMPTZ`.
- Índice `idx_sessoes_user_email`: `ON sessoes (LOWER(user_email))`.
- Tabela `admin_audit_events`: Trilha persistida com `action`, `actor`, `correlation_id`, `status`, `details JSONB`.
- Reconciliação seletiva: Apenas registros com proprietário inequívoco são migrados. Registros com colisão são preservados em `conversas` para resolução manual.

---

## 6. Verificações de Homologação Pós-Migração
Execute as seguintes consultas de validação para comprovar a consistência e isolamento:

```sql
-- 1. Verificar registro formal da migração
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- 2. Verificar contagem de sessões migradas
SELECT COUNT(*) AS total_sessoes_reconciliadas FROM sessoes;

-- 3. Garantir unicidade absoluta de session_id
SELECT session_id, COUNT(*) 
FROM sessoes 
GROUP BY session_id 
HAVING COUNT(*) > 1;

-- 4. Teste de isolamento multi-tenant (tentativa de colisão)
-- A inserção abaixo DEVE colidir na restrição de chave primária:
INSERT INTO sessoes (session_id, user_email, project_id)
VALUES ('sess_teste_existente', 'outro_usuario@helpusbr.com', 'general')
ON CONFLICT (session_id) DO NOTHING;

-- 5. Teste da trilha de auditoria persistida
SELECT COUNT(*) FROM admin_audit_events;
```

---

## 7. Procedimento de Rollback de Emergência
Caso ocorra qualquer divergência ou bloqueio operacional durante a homologação em staging:

```sql
BEGIN;

-- 1. Remoção do registro de versão
DELETE FROM schema_migrations WHERE version = '003_sessoes_schema_and_diagnostic';

-- 2. Remoção dos índices e tabelas
DROP INDEX IF EXISTS idx_admin_audit_events_created;
DROP TABLE IF EXISTS admin_audit_events CASCADE;
DROP INDEX IF EXISTS idx_sessoes_user_email;
DROP TABLE IF EXISTS sessoes CASCADE;

COMMIT;
```

Se for necessária a restauração completa a partir do backup físico:
```bash
pg_restore --clean --if-exists -v -d "${DATABASE_URL}" "${BACKUP_FILE}"
```
