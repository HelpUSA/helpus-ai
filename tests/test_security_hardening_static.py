import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
"""Regression checks for public-surface HelpUS security invariants.

These static checks intentionally run without live provider credentials, a database,
or invoking the local bridge.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SecurityHardeningTests(unittest.TestCase):
    def test_admin_denies_empty_allowlist(self):
        source = (ROOT / "api" / "auth.py").read_text(encoding="utf-8")
        self.assertIn("if not ADMIN_EMAILS or email not in ADMIN_EMAILS:", source)
        mirror = (ROOT / "backend" / "auth.py").read_text(encoding="utf-8")
        self.assertIn("if not ADMIN_EMAILS or email not in ADMIN_EMAILS:", mirror)

    def test_public_stream_has_no_local_execution_trigger(self):
        source = (ROOT / "api" / "main.py").read_text(encoding="utf-8")
        stream = source.split('@app.post("/chat/stream")', 1)[1]
        stream = stream.split('@app.post("/internal/smoke-chat-auth-flow"', 1)[0]
        self.assertNotIn("executar_no_computador_local(", stream)
        self.assertNotIn("detectar_intencao_local(", stream)
        mirror = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
        mirror_stream = mirror.split('@app.post("/chat/stream")', 1)[1]
        mirror_stream = mirror_stream.split('@app.post("/internal/smoke-chat-auth-flow"', 1)[0]
        self.assertNotIn("executar_no_computador_local(", mirror_stream)
        self.assertNotIn("detectar_intencao_local(", mirror_stream)

    def test_prompt_does_not_claim_total_local_access(self):
        source = (ROOT / "api" / "cerebro.py").read_text(encoding="utf-8")
        self.assertNotIn("Voce tem permissao total para acessar arquivos", source)
        mirror = (ROOT / "backend" / "cerebro.py").read_text(encoding="utf-8")
        self.assertNotIn("Voce tem permissao total para acessar arquivos", mirror)

    def test_tenant_isolation_queries_do_not_leak_anonymous_rows(self):
        for path in [ROOT / "api" / "banco.py", ROOT / "backend" / "banco.py"]:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("WHERE (LOWER(user_email) = %s OR user_email IS NULL)", source)
            self.assertNotIn("AND (LOWER(user_email) = %s OR user_email IS NULL)", source)
            self.assertIn("WHERE session_id = %s AND LOWER(user_email) = %s", source)
            self.assertIn("WHERE LOWER(user_email) = %s", source)

    def test_model_allowlist_validation(self):
        from backend.main import ALLOWED_MODELS, validar_modelo
        from fastapi import HTTPException

        self.assertIn("gemini-2.5-flash", ALLOWED_MODELS)
        self.assertIn("deepseek-chat", ALLOWED_MODELS)
        self.assertEqual(validar_modelo("GEMINI-2.5-FLASH"), "gemini-2.5-flash")
        self.assertIsNone(validar_modelo(None))
        self.assertIsNone(validar_modelo(""))

        with self.assertRaises(HTTPException) as ctx:
            validar_modelo("untrusted-model-exploit-v1")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_chat_endpoints_enforce_tenant_scoped_history(self):
        for path in [ROOT / "api" / "main.py", ROOT / "backend" / "main.py"]:
            source = path.read_text(encoding="utf-8")
            self.assertIn("carregar_mensagens(session_id, limite=10, user_email=user_email)", source)
            self.assertIn("carregar_mensagens(session_id, limite=6, user_email=user_email)", source)

if __name__ == "__main__":
    unittest.main()
