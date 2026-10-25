-- HelpUS AI - Migration 003: Sessoes Schema, Admin Audit Trail & Strict Non-Ambiguous Reconciliation
-- Target: Remote PostgreSQL (Staging / Production)
-- Safety: Additive, Idempotent, Conflict-aware (Zero arbitrary election of owner or project)
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
-- A. Diagnostico de conflito multi-usuario (proprietarios distintos na mesma sessao):
-- SELECT session_id, COUNT(DISTINCT LOWER(user_email)) AS num_owners,
--        ARRAY_AGG(DISTINCT LOWER(user_email)) AS conflicting_emails
-- FROM conversas
-- WHERE session_id IS NOT NULL AND session_id != ''
-- GROUP BY session_id
-- HAVING COUNT(DISTINCT LOWER(user_email)) > 1;

-- B. Diagnostico de mistura de anonimo (NULL/vazio) e autenticado na mesma sessao:
-- SELECT session_id,
--        COUNT(CASE WHEN user_email IS NULL OR TRIM(user_email) = '' THEN 1 END) AS msgs_anonimas,
--        COUNT(CASE WHEN user_email IS NOT NULL AND TRIM(user_email) != '' THEN 1 END) AS msgs_autenticadas,
--        ARRAY_AGG(DISTINCT LOWER(user_email)) FILTER (WHERE user_email IS NOT NULL AND TRIM(user_email) != '') AS emails
-- FROM conversas
-- WHERE session_id IS NOT NULL AND session_id != ''
-- GROUP BY session_id
-- HAVING COUNT(CASE WHEN user_email IS NULL OR TRIM(user_email) = '' THEN 1 END) > 0
--    AND COUNT(CASE WHEN user_email IS NOT NULL AND TRIM(user_email) != '' THEN 1 END) > 0;

-- C. Diagnostico de sessao com multiplos project_id (ambiguidade de projeto):
-- SELECT session_id, LOWER(user_email) AS owner,
--        COUNT(DISTINCT COALESCE(project_id, 'general')) AS num_projetos,
--        ARRAY_AGG(DISTINCT COALESCE(project_id, 'general')) AS projetos_em_conflito
-- FROM conversas
-- WHERE session_id IS NOT NULL AND session_id != ''
-- GROUP BY session_id, LOWER(user_email)
-- HAVING COUNT(DISTINCT COALESCE(project_id, 'general')) > 1;

-- 4. RECONCILIACAO SEGURA, CONTROLADA E NAO-AMBIGUA (P0):
-- Migra estritamente sessoes unívocas:
-- 1. Exatamente 1 proprietario autenticado
-- 2. Zero mistura de mensagens anonimas com autenticadas
-- 3. Exatamente 1 project_id atribuido no historico legado
INSERT INTO sessoes (session_id, user_email, project_id, created_at)
SELECT c.session_id, LOWER(c.user_email), COALESCE(c.project_id, 'general'), MIN(c.created_at)
FROM conversas c
WHERE c.session_id IS NOT NULL 
  AND c.session_id != ''
  AND c.user_email IS NOT NULL
  AND TRIM(c.user_email) != ''
GROUP BY c.session_id, LOWER(c.user_email), COALESCE(c.project_id, 'general')
HAVING c.session_id NOT IN (
    -- Subquery de exclusao 1: Conflito multi-usuario
    SELECT session_id
    FROM conversas
    WHERE session_id IS NOT NULL AND session_id != ''
    GROUP BY session_id
    HAVING COUNT(DISTINCT LOWER(user_email)) > 1

    UNION

    -- Subquery de exclusao 2: Mistura de anonimo e autenticado
    SELECT session_id
    FROM conversas
    WHERE session_id IS NOT NULL AND session_id != ''
    GROUP BY session_id
    HAVING COUNT(CASE WHEN user_email IS NULL OR TRIM(user_email) = '' THEN 1 END) > 0
       AND COUNT(CASE WHEN user_email IS NOT NULL AND TRIM(user_email) != '' THEN 1 END) > 0

    UNION

    -- Subquery de exclusao 3: Multiplos projetos na mesma sessao (impede escolha arbitraria)
    SELECT session_id
    FROM conversas
    WHERE session_id IS NOT NULL AND session_id != ''
    GROUP BY session_id
    HAVING COUNT(DISTINCT COALESCE(project_id, 'general')) > 1
)
ON CONFLICT (session_id) DO NOTHING;

-- 5. Registro formal da versao aplicada
INSERT INTO schema_migrations (version, description)
VALUES ('003_sessoes_schema_and_diagnostic', 'Authoritative sessoes table, admin audit log, and strict non-ambiguous reconciliation')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK DDL:
-- BEGIN;
-- DELETE FROM schema_migrations WHERE version = '003_sessoes_schema_and_diagnostic';
-- DROP INDEX IF EXISTS idx_admin_audit_events_created;
-- DROP TABLE IF EXISTS admin_audit_events CASCADE;
-- DROP INDEX IF EXISTS idx_sessoes_user_email;
-- DROP TABLE IF EXISTS sessoes CASCADE;
-- COMMIT;
-- ============================================================================
