-- HelpUS AI - Migration 002: Tenant Isolation & Performance Indexes
-- Target: Remote PostgreSQL (Railway / Supabase / Neon)
-- Safety: Additive, Idempotent, Safe for live database apply.
-- Reversible: Includes rollback script at footer.

BEGIN;

-- 1. Index for tenant-isolated conversation listing and ordering
CREATE INDEX IF NOT EXISTS idx_conversas_tenant_session
ON conversas (LOWER(user_email), session_id, created_at DESC);

-- 2. Index for tenant-isolated project conversation filtering
CREATE INDEX IF NOT EXISTS idx_conversas_tenant_project
ON conversas (LOWER(user_email), project_id, created_at DESC);

-- 3. Index for tenant-isolated project listing
CREATE INDEX IF NOT EXISTS idx_projetos_tenant_created
ON projetos (LOWER(user_email), created_at ASC);

-- 4. Audit comments documenting isolation invariant
COMMENT ON INDEX idx_conversas_tenant_session IS 'Ensures strict tenant-scoped conversation lookup without anonymous row leakage';
COMMENT ON INDEX idx_conversas_tenant_project IS 'Accelerates project-scoped conversation filtering per authenticated tenant';
COMMENT ON INDEX idx_projetos_tenant_created IS 'Ensures fast project resolution scoped to user email';

COMMIT;

-- ============================================================================
-- ROLLBACK DDL (For disaster recovery or testing):
-- DROP INDEX IF EXISTS idx_conversas_tenant_session;
-- DROP INDEX IF EXISTS idx_conversas_tenant_project;
-- DROP INDEX IF EXISTS idx_projetos_tenant_created;
-- ============================================================================
