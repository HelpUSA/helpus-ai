"""Adversarial and functional validation tests for Migration 003:
Authoritative sessoes reconciliation, conflict diagnostic, and rollback safety.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ["HELPUS_TEST_MODE"] = "1"

class Migration003ReconciliationTests(unittest.TestCase):
    def test_reconciliation_diagnostic_categorizes_legacy_conflicts_strictly(self):
        """Valida que o diagnóstico de reconciliação categoriza corretamente:
        - Conflitos multi-usuário
        - Mistura de anônimo e autenticado
        - Multiplos projetos na mesma sessão
        """
        from migrations.reconcile_sessoes_diagnostic import diagnosticar_sessoes_legadas
        
        # Simula consultas com psycopg mockado
        with patch("psycopg.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            
            # 1. Total de sessões
            # 2. Multi-usuário (> 1 owner)
            # 3. Mistura anônimo + autenticado
            # 4. Multi-projeto
            mock_cur.fetchone.return_value = [10]
            mock_cur.fetchall.side_effect = [
                # Multi-usuário
                [("sess_multi_user", 2, ["alice@helpus.com", "bob@helpus.com"], 5)],
                # Mistura anônimo + autenticado
                [("sess_mixed_anon", 2, 3, ["alice@helpus.com"])],
                # Multi-projeto
                [("sess_multi_proj", "alice@helpus.com", 2, ["general", "finance"])]
            ]
            
            report = diagnosticar_sessoes_legadas("postgresql://fake:fake@localhost:5432/db")
            self.assertTrue(report["ok"])
            self.assertEqual(report["total_sessoes_legadas"], 10)
            self.assertEqual(len(report["conflitos_multi_usuario"]), 1)
            self.assertEqual(report["conflitos_multi_usuario"][0]["session_id"], "sess_multi_user")
            self.assertEqual(len(report["conflitos_mistura_anonimo"]), 1)
            self.assertEqual(report["conflitos_mistura_anonimo"][0]["session_id"], "sess_mixed_anon")
            self.assertEqual(len(report["conflitos_multi_projeto"]), 1)
            self.assertEqual(report["conflitos_multi_projeto"][0]["session_id"], "sess_multi_proj")

    def test_migration_003_sql_excludes_ambiguous_sessions_from_sessoes(self):
        """Verifica que o arquivo SQL 003 contém as subqueries de exclusão para não migrar
        sessões ambíguas ou conflitantes."""
        sql_path = Path(__file__).resolve().parents[1] / "migrations" / "003_sessoes_schema_and_diagnostic.sql"
        self.assertTrue(sql_path.exists(), "Arquivo SQL 003 deve existir")
        sql_content = sql_path.read_text(encoding="utf-8")
        
        # Subquery de exclusão 1: Conflito multi-usuário
        self.assertIn("COUNT(DISTINCT LOWER(user_email)) > 1", sql_content)
        # Subquery de exclusão 2: Mistura de anônimo e autenticado
        self.assertIn("COUNT(CASE WHEN user_email IS NULL OR TRIM(user_email) = '' THEN 1 END) > 0", sql_content)
        # Subquery de exclusão 3: Multiplos projetos
        self.assertIn("COUNT(DISTINCT COALESCE(project_id, 'general')) > 1", sql_content)
        # Inserção formal de versão
        self.assertIn("INSERT INTO schema_migrations (version, description)", sql_content)
        self.assertIn("'003_sessoes_schema_and_diagnostic'", sql_content)
        # Rollback DDL
        self.assertIn("DELETE FROM schema_migrations WHERE version = '003_sessoes_schema_and_diagnostic'", sql_content)

    def test_schema_verification_fails_closed_when_migration_table_empty(self):
        """Garante que criar_tabelas em modo persistente levanta RuntimeError se schema_migrations estiver vazia."""
        import asyncio
        from backend.banco import BancoDados
        
        banco_test = BancoDados()
        banco_test.database_url = "postgresql://user:pass@localhost:5432/helpus_test"
        
        with patch.object(banco_test, "pool") as mock_pool:
            mock_conn = MagicMock()
            mock_cur = AsyncMock()
            mock_pool.connection.return_value.__aenter__.return_value = mock_conn
            mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
            mock_conn.cursor.return_value.__aexit__.return_value = None
            
            # Tabelas presentes, mas nenhuma migration registrada
            mock_cur.fetchall.side_effect = [
                [("conversas",), ("admin_audit_events",), ("schema_migrations",), ("sessoes",)],
                [] # schema_migrations vazio!
            ]
            
            with self.assertRaises(RuntimeError) as ctx:
                asyncio.run(banco_test.criar_tabelas())
            
            self.assertIn("Migracoes nominais obrigatorias ausentes no banco persistente", str(ctx.exception))
            self.assertIn("003_sessoes_schema_and_diagnostic", str(ctx.exception))

    def test_migration_004_turn_idempotency_ledger_sql_structure(self):
        """Verifica a integridade do DDL da Migration 004 (Turn Idempotency Ledger)."""
        sql_path = Path(__file__).resolve().parents[1] / "migrations" / "004_turn_idempotency_ledger.sql"
        self.assertTrue(sql_path.exists(), "Arquivo SQL 004 deve existir")
        sql_content = sql_path.read_text(encoding="utf-8")
        
        self.assertIn("CREATE TABLE IF NOT EXISTS turn_idempotency_ledger", sql_content)
        self.assertIn("idempotency_key VARCHAR(160) PRIMARY KEY", sql_content)
        self.assertIn("owner_token VARCHAR(80) NOT NULL", sql_content)
        self.assertIn("status VARCHAR(30) NOT NULL DEFAULT 'in_progress'", sql_content)
        self.assertIn("response_payload JSONB", sql_content)
        self.assertIn("INSERT INTO schema_migrations (version, description)", sql_content)
        self.assertIn("'004_turn_idempotency_ledger'", sql_content)
        # Rollback presente
        self.assertIn("DROP TABLE IF EXISTS turn_idempotency_ledger CASCADE", sql_content)

if __name__ == "__main__":
    unittest.main()
