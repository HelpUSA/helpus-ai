-- HelpUS AI - Migration 005: Conversas Turn Idempotency Key & Deduplication
-- Target: Remote PostgreSQL (Staging / Production)
-- Purpose: Database-level exactly-once assistant message deduplication per turn

BEGIN;

-- 1. Adiciona coluna turn_idempotency_key a tabela conversas
ALTER TABLE conversas
ADD COLUMN IF NOT EXISTS turn_idempotency_key VARCHAR(160);

-- 2. Cria indice unico parcial para mensagens de assistant com turn_idempotency_key
-- Permite retrocompatibilidade total com mensagens legadas sem violar unicidade
CREATE UNIQUE INDEX IF NOT EXISTS uq_conversas_turn_assistant
ON conversas (turn_idempotency_key)
WHERE turn_idempotency_key IS NOT NULL AND role = 'assistant';

-- 3. Indice para buscas eficientes por chave de turno
CREATE INDEX IF NOT EXISTS idx_conversas_turn_key
ON conversas (turn_idempotency_key);

-- 4. Registro formal da migration 005
INSERT INTO schema_migrations (version, description)
VALUES ('005_conversas_turn_idempotency_key', 'Turn idempotency key on conversas with unique partial constraint for assistant deduplication')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK DDL:
-- BEGIN;
-- DELETE FROM schema_migrations WHERE version = '005_conversas_turn_idempotency_key';
-- DROP INDEX IF EXISTS idx_conversas_turn_key;
-- DROP INDEX IF EXISTS uq_conversas_turn_assistant;
-- ALTER TABLE conversas DROP COLUMN IF EXISTS turn_idempotency_key;
-- COMMIT;
-- ============================================================================
