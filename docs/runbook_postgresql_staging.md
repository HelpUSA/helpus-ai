# HelpUS AI — Runbook de Homologação e Migração PostgreSQL (Staging)

> **Status Atual de Execução Remota**: `BLOCKED` (Aguardando liberação de credenciais seguras pelo Master SuperAdmin).  
> **Escopo**: Banco de dados relacional PostgreSQL do ambiente de Staging. Nenhuma execução direta em Produção é permitida nesta etapa.

---

## 1. Pré-Requisitos e Fencing de Segurança
1. Certificar-se de que a variável `DATABASE_URL` aponte exclusivamente para a instância isolada de **Staging** (ex: `staging-db.helpusbr.com`).
2. Jamais expor segredos, tokens de serviço ou strings de conexão no código-fonte, branches públicas ou issues do GitHub.
3. Confirmar que a branch ativa seja `feature/ui-ux-modernization-v1`.

---

## 2. Procedimento de Backup Pré-Migração
Antes de aplicar qualquer migração DDL em staging, execute o backup físico/lógico completo:

```bash
# 1. Definir carimbo de data/hora
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_helpus_staging_pre_mig002_${TIMESTAMP}.dump"

# 2. Executar dump custom format (compactado e transacional)
pg_dump -Fc -v -d "${DATABASE_URL}" -f "${BACKUP_FILE}"

# 3. Validar integridade e tamanho do arquivo gerado
ls -lh "${BACKUP_FILE}"
pg_restore -l "${BACKUP_FILE}" | head -n 20
```

---

## 3. Teste de Restauração em Sandbox
Valide o backup gerado restaurando-o em um schema temporário de teste para garantir a recuperabilidade dos dados:

```bash
# 1. Criar banco/schema efêmero de verificação
createdb -h localhost -U postgres helpus_staging_verify_temp

# 2. Restaurar backup para teste
pg_restore --clean --if-exists -d helpus_staging_verify_temp "${BACKUP_FILE}"

# 3. Limpeza do banco de teste após validação bem-sucedida
dropdb -h localhost -U postgres helpus_staging_verify_temp
```

---

## 4. Aplicação da Migration 002 (Tabela Atômica `sessoes`)
A migração 002 estabelece a entidade relacional de posse de sessão e reconcilia o histórico legado da tabela `conversas`.

### Script SQL Transacional (`migrations/002_create_sessoes_table.sql`):
```sql
BEGIN;

-- 1. Criação da tabela de sessões
CREATE TABLE IF NOT EXISTS sessoes (
    session_id VARCHAR(120) PRIMARY KEY,
    user_email VARCHAR(255),
    project_id VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Índice para consultas rápidas por tenant/usuário
CREATE INDEX IF NOT EXISTS idx_sessoes_user_email
ON sessoes(LOWER(user_email));

-- 3. Reconciliação do histórico legado existente na tabela conversas
INSERT INTO sessoes (session_id, user_email, project_id, created_at)
SELECT 
    session_id, 
    LOWER(user_email), 
    COALESCE(project_id, 'general'), 
    MIN(created_at)
FROM conversas
WHERE session_id IS NOT NULL AND session_id != ''
GROUP BY session_id, LOWER(user_email), COALESCE(project_id, 'general')
ON CONFLICT (session_id) DO NOTHING;

COMMIT;
```

---

## 5. Verificações de Homologação Pós-Migração
Execute as seguintes consultas de validação para comprovar a consistência e isolamento entre contas:

```sql
-- 1. Verificar contagem de sessões migradas
SELECT COUNT(*) AS total_sessoes FROM sessoes;

-- 2. Garantir unicidade absoluta de session_id
SELECT session_id, COUNT(*) 
FROM sessoes 
GROUP BY session_id 
HAVING COUNT(*) > 1;

-- 3. Teste de isolamento multi-tenant (tentativa de colisão)
-- A inserção abaixo DEVE falhar ou colidir na constraint de chave primária:
INSERT INTO sessoes (session_id, user_email, project_id)
VALUES ('sess_teste_existente', 'outro_usuario@helpusbr.com', 'general')
ON CONFLICT (session_id) DO NOTHING;
```

---

## 6. Procedimento de Rollback de Emergência
Caso ocorra qualquer divergência ou bloqueio operacional durante a homologação em staging:

```sql
BEGIN;

-- 1. Remoção dos índices e da tabela sessoes
DROP INDEX IF EXISTS idx_sessoes_user_email;
DROP TABLE IF EXISTS sessoes CASCADE;

COMMIT;
```

Se for necessária a restauração completa a partir do backup físico:
```bash
pg_restore --clean --if-exists -v -d "${DATABASE_URL}" "${BACKUP_FILE}"
```
