-- HelpUS AI - Migration 004: Turn Idempotency Ledger & Durable Fencing
-- Target: Remote PostgreSQL (Staging / Production)
-- Purpose: Exactly-once turn execution, process-crash recovery, and durable fencing

BEGIN;

CREATE TABLE IF NOT EXISTS turn_idempotency_ledger (
    idempotency_key VARCHAR(160) PRIMARY KEY,
    owner_token VARCHAR(80) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress',
    session_id VARCHAR(120) NOT NULL,
    user_email VARCHAR(255),
    project_id VARCHAR(100) DEFAULT 'general',
    request_payload_hash VARCHAR(64) NOT NULL,
    response_payload JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    CONSTRAINT chk_turn_ledger_status CHECK (status IN ('in_progress', 'completed', 'released', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_turn_ledger_session
ON turn_idempotency_ledger (session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_turn_ledger_status_heartbeat
ON turn_idempotency_ledger (status, last_heartbeat);

CREATE INDEX IF NOT EXISTS idx_turn_ledger_expires
ON turn_idempotency_ledger (expires_at);

-- Registro formal da migration 004
INSERT INTO schema_migrations (version, description)
VALUES ('004_turn_idempotency_ledger', 'Durable turn idempotency ledger with state machine, retention and fencing token')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK DDL:
-- BEGIN;
-- DELETE FROM schema_migrations WHERE version = '004_turn_idempotency_ledger';
-- DROP INDEX IF EXISTS idx_turn_ledger_expires;
-- DROP INDEX IF EXISTS idx_turn_ledger_status_heartbeat;
-- DROP INDEX IF EXISTS idx_turn_ledger_session;
-- DROP TABLE IF EXISTS turn_idempotency_ledger CASCADE;
-- COMMIT;
-- ============================================================================
