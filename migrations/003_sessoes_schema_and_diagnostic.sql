-- HelpUS AI - Migration 003: Sessoes Schema, Admin Audit Trail & Conflict-Aware Reconciliation
-- Target: Remote PostgreSQL (Staging / Production)
-- Safety: Additive, Idempotent, Conflict-aware (No silent arbitrary owner election)
-- Reversible: Includes rollback script at footer.

BEGIN;

-- 0. Schema Migration History Tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 1. Tabela Autorizativa de Posse de Sessao
CREATE TABLE IF NOT EXISTS sessoes (
    session_id VARCHAR(120) PRIMARY KEY,
    user_email VARCHAR(255),
    project_id VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessoes_user_email
ON sessoes (LOWER(user_email));

-- 2. Tabela de Trilha de Auditoria Administrativa Persistida
CREATE TABLE IF NOT EXISTS admin_audit_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    correlation_id VARCHAR(120),
    status VARCHAR(50) DEFAULT 'success',
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_events_created
ON admin_audit_events (created_at DESC);

-- 3. ETAPA DIAGNOSTICA PRE-MIGRACAO (READ-ONLY):
-- Consulta analitica para inspecao de sessoes legadas com multiplos usuarios/projetos:
-- SELECT session_id, COUNT(DISTINCT LOWER(user_email)) AS distinct_owners,
--        ARRAY_AGG(DISTINCT LOWER(user_email)) AS conflicting_emails,
--        MIN(created_at) AS first_seen, MAX(created_at) AS last_seen
-- FROM conversas
-- WHERE session_id IS NOT NULL AND session_id != ''
-- GROUP BY session_id
-- HAVING COUNT(DISTINCT LOWER(user_email)) > 1;

-- 4. RECONCILIACAO SEGURA E CONTROLADA:
-- Migra apenas sessoes limpas e inequivocas (exatamente 1 usuario proprietario).
-- Sessoes com conflito multi-usuario NAO sao arbitadas silenciosamente; sao mantidas para reconciliacao auditada.
INSERT INTO sessoes (session_id, user_email, project_id, created_at)
SELECT c.session_id, LOWER(c.user_email), COALESCE(c.project_id, 'general'), MIN(c.created_at)
FROM conversas c
WHERE c.session_id IS NOT NULL AND c.session_id != ''
GROUP BY c.session_id, LOWER(c.user_email), COALESCE(c.project_id, 'general')
HAVING c.session_id NOT IN (
    -- Exclui qualquer session_id que possua mais de um usuario distinto no historico legado
    SELECT session_id
    FROM conversas
    WHERE session_id IS NOT NULL AND session_id != ''
    GROUP BY session_id
    HAVING COUNT(DISTINCT LOWER(user_email)) > 1
)
ON CONFLICT (session_id) DO NOTHING;

-- 5. Registro da versao aplicada
INSERT INTO schema_migrations (version, description)
VALUES ('003_sessoes_schema_and_diagnostic', 'Authoritative sessoes table, admin audit log, and conflict-aware reconciliation')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK DDL (Para recuperacao de desastre ou testes em sandbox):
-- BEGIN;
-- DELETE FROM schema_migrations WHERE version = '003_sessoes_schema_and_diagnostic';
-- DROP INDEX IF EXISTS idx_admin_audit_events_created;
-- DROP TABLE IF EXISTS admin_audit_events CASCADE;
-- DROP INDEX IF EXISTS idx_sessoes_user_email;
-- DROP TABLE IF EXISTS sessoes CASCADE;
-- COMMIT;
-- ============================================================================
