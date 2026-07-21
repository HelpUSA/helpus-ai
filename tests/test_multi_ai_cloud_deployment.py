
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class MultiAiCloudDeploymentTests(unittest.TestCase):
    def test_router_dockerfile_uses_railway_port(self) -> None:
        path = (
            REPO
            / "services"
            / "multi_ai_router"
            / "Dockerfile"
        )
        content = path.read_text(encoding="utf-8")

        self.assertIn("${PORT:-8080}", content)
        self.assertIn('"sh","-c"', content)
        self.assertIn("exec uvicorn", content)
        self.assertNotIn(
            '"--port","8080"',
            content,
        )

    def test_router_readyz_checks_litellm(self) -> None:
        path = (
            REPO
            / "services"
            / "multi_ai_router"
            / "app.py"
        )
        content = path.read_text(encoding="utf-8")

        ast.parse(content)

        self.assertIn(
            'HELPUS_GATEWAY_BASE_URL',
            content,
        )
        self.assertIn(
            '/health/liveliness',
            content,
        )
        self.assertIn(
            '_helpus_url_request.urlopen',
            content,
        )
        self.assertIn(
            'status_code=503',
            content,
        )
        self.assertIn(
            '"gateway": "unreachable"',
            content,
        )

    def test_litellm_dockerfile_uses_railway_port(self) -> None:
        path = (
            REPO
            / "infra"
            / "multi-ai"
            / "Dockerfile.litellm"
        )
        content = path.read_text(encoding="utf-8")

        self.assertIn(
            "docker.litellm.ai/berriai/litellm",
            content,
        )
        self.assertIn(
            "litellm-config.yaml",
            content,
        )
        self.assertIn(
            "${PORT:-4000}",
            content,
        )
        self.assertIn(
            "exec litellm",
            content,
        )

    def test_router_railway_config(self) -> None:
        path = (
            REPO
            / "infra"
            / "multi-ai"
            / "railway-router.json"
        )
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            data["build"]["builder"],
            "DOCKERFILE",
        )
        self.assertEqual(
            data["build"]["dockerfilePath"],
            "services/multi_ai_router/Dockerfile",
        )
        self.assertEqual(
            data["deploy"]["healthcheckPath"],
            "/readyz",
        )
        self.assertIn(
            "services/multi_ai_router/**",
            data["build"]["watchPatterns"],
        )

    def test_litellm_railway_config(self) -> None:
        path = (
            REPO
            / "infra"
            / "multi-ai"
            / "railway-litellm.json"
        )
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            data["build"]["builder"],
            "DOCKERFILE",
        )
        self.assertEqual(
            data["build"]["dockerfilePath"],
            "infra/multi-ai/Dockerfile.litellm",
        )
        self.assertEqual(
            data["deploy"]["healthcheckPath"],
            "/health/liveliness",
        )
        self.assertIn(
            "infra/multi-ai/litellm-config.yaml",
            data["build"]["watchPatterns"],
        )

    def test_package_runs_cloud_tests(self) -> None:
        package_path = REPO / "package.json"
        package = json.loads(
            package_path.read_text(encoding="utf-8")
        )

        scripts = package["scripts"]

        self.assertIn(
            "test:multi-ai-cloud",
            scripts,
        )
        self.assertIn(
            "npm run test:multi-ai-cloud",
            scripts["test:multi-ai-integration"],
        )


if __name__ == "__main__":
    unittest.main()
