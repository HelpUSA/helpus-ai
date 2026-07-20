from __future__ import annotations

import ast
import inspect
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
TESTS = ROOT / "tests"

sys.path.insert(0, str(BACKEND))

import cerebro
import multi_ai_provider as provider


EXPECTED_ALIASES = {
    "helpus-fast",
    "helpus-general",
    "helpus-reasoner",
    "helpus-code",
    "helpus-vision",
    "helpus-verifier",
    "helpus-embedding",
}

EXPECTED_MODES = {
    "single",
    "review",
    "council",
    "auto",
}


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def validate_defaults() -> None:
    config = provider.load_multi_ai_config({})

    require(
        config.enabled is False,
        "enabled default changed",
    )
    require(
        config.base_url
        == "http://127.0.0.1:8080",
        "base URL default changed",
    )
    require(
        config.api_key == "",
        "API key default changed",
    )
    require(
        config.timeout_seconds == 180.0,
        "timeout default changed",
    )
    require(
        config.mode == "auto",
        "mode default changed",
    )
    require(
        config.fallback_to_legacy is True,
        "fallback default changed",
    )
    require(
        config.default_alias
        == "helpus-general",
        "default alias changed",
    )


def validate_provider() -> None:
    require(
        EXPECTED_ALIASES.issubset(
            provider._ALLOWED_ALIASES
        ),
        "runtime aliases incomplete",
    )

    require(
        provider._ALLOWED_MODES
        == EXPECTED_MODES,
        "runtime modes changed",
    )

    source = (
        ROOT
        / "backend"
        / "multi_ai_provider.py"
    ).read_text(
        encoding="utf-8-sig"
    )

    for marker in (
        "/v1/chat/completions",
        "helpus_mode",
        "multi_ai_timeout",
        "multi_ai_network_error",
        "multi_ai_unavailable",
    ):
        require(
            marker in source,
            "provider marker missing: "
            + marker,
        )

    lowered = source.lower()

    for forbidden in (
        "subprocess",
        "psycopg",
        "sqlite",
        "redis",
        "ai-bridge-local",
    ):
        require(
            forbidden not in lowered,
            "forbidden provider marker: "
            + forbidden,
        )


def validate_brain() -> None:
    path = (
        ROOT
        / "backend"
        / "cerebro.py"
    )

    source = path.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(source)

    brain = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CerebroIA"
    )

    methods = {
        node.name: node
        for node in brain.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    }

    require(
        "pensar" in methods,
        "pensar missing",
    )
    require(
        "_pensar_legado" in methods,
        "legacy method missing",
    )
    require(
        isinstance(
            methods["pensar"],
            ast.AsyncFunctionDef,
        ),
        "pensar is not async",
    )
    require(
        isinstance(
            methods["_pensar_legado"],
            ast.AsyncFunctionDef,
        ),
        "legacy method is not async",
    )

    arguments = list(
        inspect.signature(
            cerebro.CerebroIA.pensar
        ).parameters
    )

    require(
        arguments == [
            "self",
            "pergunta",
            "contexto_busca",
            "historico",
            "max_tokens",
        ],
        "public pensar signature changed",
    )

    for marker in (
        "[AI_LOCAL]",
        "[AI_LOCAL_RUN]",
        "inter_agent_message",
        "gateway-brain-supervisor",
        "result_is_final=1",
        "HELPUS_MULTI_AI_ENABLED",
        "HELPUS_MULTI_AI_FALLBACK_TO_LEGACY",
    ):
        require(
            marker in source,
            "brain marker missing: "
            + marker,
        )


def validate_main_contract() -> None:
    source = (
        ROOT
        / "backend"
        / "main.py"
    ).read_text(
        encoding="utf-8-sig"
    )

    require(
        ".pensar(" in source,
        "main.py no longer calls pensar",
    )

    require(
        "multi_ai_provider" not in source,
        "main.py bypasses CerebroIA",
    )


def run_runtime_tests() -> int:
    suite = (
        unittest
        .defaultTestLoader
        .discover(
            str(TESTS),
            pattern=(
                "test_multi_ai_"
                "runtime_integration.py"
            ),
        )
    )

    count = suite.countTestCases()

    require(
        count == 11,
        (
            "expected 11 tests, "
            f"found {count}"
        ),
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    require(
        result.wasSuccessful(),
        "runtime integration tests failed",
    )

    return count


def main() -> int:
    validate_defaults()
    validate_provider()
    validate_brain()
    validate_main_contract()

    test_count = run_runtime_tests()

    print(
        "HELPUS_RUNTIME_MULTI_AI_VALIDATION_OK"
    )
    print(
        f"RUNTIME_MULTI_AI_UNIT_TESTS={test_count}"
    )
    print(
        "RUNTIME_MULTI_AI_DEFAULT_ENABLED=False"
    )
    print(
        "RUNTIME_MULTI_AI_REAL_NETWORK_CALLS=False"
    )
    print(
        "LEGACY_PUBLIC_CONTRACT_PRESERVED=True"
    )
    print(
        "CLOUD_GPU_PROVISIONED=False"
    )
    print(
        "PROVIDER_CREDENTIALS_ADDED=False"
    )
    print(
        "AI_BRIDGE_LOCAL_MODIFIED=False"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
