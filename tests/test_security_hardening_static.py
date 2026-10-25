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

if __name__ == "__main__":
    unittest.main()
