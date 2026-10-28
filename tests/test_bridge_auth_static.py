"""Source-level regression checks; runtime client handshake is a separate gate."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class BridgeAuthInvariantTests(unittest.TestCase):
    def test_bridge_requires_dedicated_secret_in_both_backends(self):
        for directory in ("api", "backend"):
            with self.subTest(directory=directory):
                source = (ROOT / directory / "main.py").read_text(encoding="utf-8")
                self.assertIn('os.getenv("HELPUS_BRIDGE_API_TOKEN", "")', source)
                self.assertIn("hmac.compare_digest(presented, configured)", source)
                for signature in (
                    "bridge_poll(_bridge_auth: None = Depends(require_bridge_token))",
                    "bridge_result(res: BridgeResultRequest, _bridge_auth: None = Depends(require_bridge_token))",
                    "bridge_status(_bridge_auth: None = Depends(require_bridge_token))",
                ):
                    self.assertIn(signature, source)

if __name__ == "__main__":
    unittest.main()
