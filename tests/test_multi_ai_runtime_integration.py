from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT / "backend"),
)

import cerebro
from multi_ai_provider import (
    MultiAIConfig,
    MultiAIProvider,
    MultiAIProviderError,
    MultiAIResult,
    load_multi_ai_config,
    sanitize_multi_ai_error,
)


class FakeMultiProvider:
    def __init__(
        self,
        result=None,
        error=None,
    ):
        self.result = result
        self.error = error
        self.calls = []

    async def generate(
        self,
        prompt,
        max_tokens,
        temperature,
    ):
        self.calls.append(
            {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )

        if self.error is not None:
            raise self.error

        return self.result


class FakeHTTPResponse:
    status_code = 200

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": "cliente mockado ok"
                    }
                }
            ],
            "usage": {
                "completion_tokens": 12,
            },
            "_helpus": {
                "request_id": "request-http-test",
                "elapsed_ms": 45,
                "route": {
                    "mode": "single",
                    "primary": "helpus-general",
                },
            },
        }


class FakeHTTPClient:
    calls = []

    def __init__(
        self,
        timeout=None,
    ):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    async def post(
        self,
        url,
        headers=None,
        json=None,
    ):
        self.__class__.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": self.timeout,
            }
        )

        return FakeHTTPResponse()


async def legacy_success(
    self,
    pergunta,
    contexto_busca="",
    historico=None,
    max_tokens=None,
):
    self.last_provider_used = "gemini"
    self.last_fallback_reason = None

    return (
        "legado ok",
        0,
        0.01,
    )


async def legacy_failure(
    self,
    pergunta,
    contexto_busca="",
    historico=None,
    max_tokens=None,
):
    raise RuntimeError(
        "LEGACY_SECRET private payload"
    )


def multi_ai_result():
    return MultiAIResult(
        text="roteador multi-ai ok",
        tokens=17,
        latency_ms=222,
        alias="helpus-reasoner",
        mode="review",
        request_id="request-runtime-test",
    )


def make_brain(
    multi_provider=None,
    legacy_method=legacy_success,
):
    brain = object.__new__(
        cerebro.CerebroIA
    )

    brain.provider = "gemini"
    brain.nome_modelo = "gemini-test"
    brain.client = None
    brain.multi_ai_provider = multi_provider
    brain.last_provider_used = "gemini"
    brain.last_fallback_reason = None
    brain.last_multi_ai_alias = None
    brain.last_multi_ai_mode = None
    brain.last_multi_ai_request_id = None
    brain.last_multi_ai_latency_ms = None

    brain._pensar_legado = types.MethodType(
        legacy_method,
        brain,
    )

    return brain


class RuntimeIntegrationTests(
    unittest.IsolatedAsyncioTestCase
):
    def setUp(self):
        app_names = [
            "HELPUS_MULTI_AI_ENABLED",
            "HELPUS_MULTI_AI_BASE_URL",
            "HELPUS_MULTI_AI_API_KEY",
            "HELPUS_MULTI_AI_TIMEOUT_SECONDS",
            "HELPUS_MULTI_AI_MODE",
            "HELPUS_MULTI_AI_FALLBACK_TO_LEGACY",
            "HELPUS_MULTI_AI_DEFAULT_ALIAS",
            "DEEPSEEK_API_KEY",
            "OPENROUTER_API_KEY",
        ]

        self.old_app_values = {
            name: getattr(
                cerebro.app_config,
                name,
            )
            for name in app_names
        }

        self.old_ai_provider = cerebro.AI_PROVIDER
        self.old_gemini_key = cerebro.GEMINI_API_KEY

        cerebro.app_config.HELPUS_MULTI_AI_BASE_URL = (
            "http://127.0.0.1:8080"
        )
        cerebro.app_config.HELPUS_MULTI_AI_API_KEY = ""
        cerebro.app_config.HELPUS_MULTI_AI_TIMEOUT_SECONDS = (
            180.0
        )
        cerebro.app_config.HELPUS_MULTI_AI_MODE = "auto"
        cerebro.app_config.HELPUS_MULTI_AI_DEFAULT_ALIAS = (
            "helpus-general"
        )
        cerebro.app_config.DEEPSEEK_API_KEY = ""
        cerebro.app_config.OPENROUTER_API_KEY = ""

    def tearDown(self):
        for name, value in self.old_app_values.items():
            setattr(
                cerebro.app_config,
                name,
                value,
            )

        cerebro.AI_PROVIDER = self.old_ai_provider
        cerebro.GEMINI_API_KEY = self.old_gemini_key

    def test_public_contract_and_safe_defaults(self):
        self.assertTrue(
            inspect.iscoroutinefunction(
                cerebro.CerebroIA.pensar
            )
        )

        self.assertTrue(
            inspect.iscoroutinefunction(
                cerebro.CerebroIA._pensar_legado
            )
        )

        self.assertEqual(
            list(
                inspect.signature(
                    cerebro.CerebroIA.pensar
                ).parameters
            ),
            [
                "self",
                "pergunta",
                "contexto_busca",
                "historico",
                "max_tokens",
            ],
        )

        config = load_multi_ai_config({})

        self.assertFalse(config.enabled)
        self.assertEqual(
            config.base_url,
            "http://127.0.0.1:8080",
        )
        self.assertEqual(config.api_key, "")
        self.assertEqual(
            config.timeout_seconds,
            180.0,
        )
        self.assertEqual(config.mode, "auto")
        self.assertTrue(
            config.fallback_to_legacy
        )
        self.assertEqual(
            config.default_alias,
            "helpus-general",
        )

        self.assertIn(
            "helpus-embedding",
            __import__(
                "multi_ai_provider"
            )._ALLOWED_ALIASES,
        )

    def test_constructor_allows_multi_ai_without_legacy_key(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            True
        )

        for provider_name in (
            "gemini",
            "openrouter",
            "deepseek",
        ):
            with self.subTest(
                provider=provider_name
            ):
                cerebro.AI_PROVIDER = provider_name
                cerebro.GEMINI_API_KEY = ""

                brain = cerebro.CerebroIA()

                self.assertEqual(
                    brain.provider,
                    provider_name,
                )
                self.assertIsNone(
                    brain.client
                )
                self.assertIsNone(
                    brain.multi_ai_provider
                )

    def test_disabled_mode_preserves_missing_key_failure(self):
        cerebro.AI_PROVIDER = "gemini"
        cerebro.GEMINI_API_KEY = ""

        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            False
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "GEMINI_API_KEY nao configurada",
        ):
            cerebro.CerebroIA()

    async def test_disabled_flag_never_calls_router(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            False
        )

        fake_multi = FakeMultiProvider(
            result=multi_ai_result()
        )

        brain = make_brain(
            multi_provider=fake_multi
        )

        result = await brain.pensar(
            "usar caminho legado"
        )

        self.assertEqual(
            result,
            (
                "legado ok",
                0,
                0.01,
            ),
        )

        self.assertEqual(
            fake_multi.calls,
            [],
        )

        self.assertEqual(
            brain.last_provider_used,
            "gemini",
        )

    async def test_router_success_preserves_prompt_and_metadata(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            True
        )
        cerebro.app_config.HELPUS_MULTI_AI_FALLBACK_TO_LEGACY = (
            True
        )

        fake_multi = FakeMultiProvider(
            result=multi_ai_result()
        )

        brain = make_brain(
            multi_provider=fake_multi
        )

        result = await brain.pensar(
            pergunta="pergunta atual",
            contexto_busca=(
                "contexto consolidado"
            ),
            historico=[
                {
                    "role": "user",
                    "content": (
                        "historico consolidado"
                    ),
                }
            ],
            max_tokens=456,
        )

        self.assertEqual(
            result[0],
            "roteador multi-ai ok",
        )
        self.assertEqual(result[1], 17)
        self.assertIsInstance(
            result[2],
            float,
        )

        self.assertEqual(
            len(fake_multi.calls),
            1,
        )

        call = fake_multi.calls[0]
        prompt = call["prompt"]

        for marker in (
            "Voce e o HelpUS",
            "[AI_LOCAL]",
            "[AI_LOCAL_RUN]",
            "inter_agent_message",
            "gateway-brain-supervisor",
            "result_is_final=1",
            "contexto consolidado",
            "historico consolidado",
            "pergunta atual",
        ):
            self.assertIn(
                marker,
                prompt,
            )

        self.assertEqual(
            call["max_tokens"],
            456,
        )

        self.assertEqual(
            brain.last_provider_used,
            "multi_ai",
        )
        self.assertIsNone(
            brain.last_fallback_reason
        )
        self.assertEqual(
            brain.last_multi_ai_alias,
            "helpus-reasoner",
        )
        self.assertEqual(
            brain.last_multi_ai_mode,
            "review",
        )
        self.assertEqual(
            brain.last_multi_ai_request_id,
            "request-runtime-test",
        )
        self.assertEqual(
            brain.last_multi_ai_latency_ms,
            222,
        )
        self.assertEqual(
            brain.nome_modelo,
            "helpus-reasoner",
        )

    async def test_network_error_uses_legacy_fallback(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            True
        )
        cerebro.app_config.HELPUS_MULTI_AI_FALLBACK_TO_LEGACY = (
            True
        )

        brain = make_brain(
            multi_provider=FakeMultiProvider(
                error=MultiAIProviderError(
                    "multi_ai_network_error"
                )
            )
        )

        result = await brain.pensar(
            "falha de rede"
        )

        self.assertEqual(
            result[0],
            "legado ok",
        )
        self.assertEqual(
            brain.last_provider_used,
            "gemini",
        )
        self.assertEqual(
            brain.last_fallback_reason,
            "multi_ai_network_error",
        )

    async def test_timeout_uses_legacy_fallback(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            True
        )
        cerebro.app_config.HELPUS_MULTI_AI_FALLBACK_TO_LEGACY = (
            True
        )

        brain = make_brain(
            multi_provider=FakeMultiProvider(
                error=asyncio.TimeoutError(
                    "TIMEOUT_SECRET"
                )
            )
        )

        result = await brain.pensar(
            "falha por timeout"
        )

        self.assertEqual(
            result[0],
            "legado ok",
        )
        self.assertEqual(
            brain.last_fallback_reason,
            "multi_ai_timeout",
        )

    async def test_no_fallback_returns_sanitized_error(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            True
        )
        cerebro.app_config.HELPUS_MULTI_AI_FALLBACK_TO_LEGACY = (
            False
        )

        brain = make_brain(
            multi_provider=FakeMultiProvider(
                error=RuntimeError(
                    "Bearer ROUTER_SECRET private payload"
                )
            )
        )

        with self.assertRaises(
            RuntimeError
        ) as context:
            await brain.pensar(
                "sem fallback"
            )

        message = str(
            context.exception
        )

        self.assertIn(
            "multi_ai_unavailable",
            message,
        )
        self.assertNotIn(
            "ROUTER_SECRET",
            message,
        )
        self.assertNotIn(
            "private payload",
            message,
        )
        self.assertEqual(
            brain.last_provider_used,
            "multi_ai",
        )
        self.assertEqual(
            brain.last_fallback_reason,
            "multi_ai_unavailable",
        )

    async def test_router_and_legacy_failure_are_sanitized(self):
        cerebro.app_config.HELPUS_MULTI_AI_ENABLED = (
            True
        )
        cerebro.app_config.HELPUS_MULTI_AI_FALLBACK_TO_LEGACY = (
            True
        )

        brain = make_brain(
            multi_provider=FakeMultiProvider(
                error=RuntimeError(
                    "Bearer ROUTER_SECRET"
                )
            ),
            legacy_method=legacy_failure,
        )

        with self.assertRaises(
            RuntimeError
        ) as context:
            await brain.pensar(
                "falha dupla"
            )

        message = str(
            context.exception
        )

        self.assertIn(
            "multi_ai_unavailable",
            message,
        )
        self.assertNotIn(
            "ROUTER_SECRET",
            message,
        )
        self.assertNotIn(
            "LEGACY_SECRET",
            message,
        )
        self.assertEqual(
            brain.last_fallback_reason,
            "multi_ai_unavailable_legacy_failed",
        )

    async def test_http_client_contract_without_network(self):
        FakeHTTPClient.calls = []

        config = MultiAIConfig(
            enabled=True,
            base_url="http://127.0.0.1:8080",
            api_key="mock-api-key",
            timeout_seconds=180.0,
            mode="auto",
            fallback_to_legacy=True,
            default_alias="helpus-general",
        )

        provider = MultiAIProvider(
            config=config,
            client_factory=FakeHTTPClient,
        )

        result = await provider.generate(
            prompt="prompt completo HelpUS",
            max_tokens=800,
            temperature=0.7,
        )

        self.assertEqual(
            result.text,
            "cliente mockado ok",
        )
        self.assertEqual(
            result.tokens,
            12,
        )
        self.assertEqual(
            result.latency_ms,
            45,
        )

        self.assertEqual(
            len(FakeHTTPClient.calls),
            1,
        )

        call = FakeHTTPClient.calls[0]

        self.assertEqual(
            call["url"],
            (
                "http://127.0.0.1:8080"
                "/v1/chat/completions"
            ),
        )
        self.assertEqual(
            call["headers"]["Authorization"],
            "Bearer mock-api-key",
        )
        self.assertEqual(
            call["json"]["model"],
            "helpus-general",
        )
        self.assertEqual(
            call["json"]["helpus_mode"],
            "auto",
        )
        self.assertFalse(
            call["json"]["stream"]
        )
        self.assertEqual(
            call["json"]["messages"][0]["content"],
            "prompt completo HelpUS",
        )

    def test_sanitizer_does_not_expose_exception_message(self):
        error = RuntimeError(
            "Bearer SANITIZER_SECRET private data"
        )

        self.assertEqual(
            sanitize_multi_ai_error(error),
            "multi_ai_unavailable",
        )

        self.assertNotIn(
            "SANITIZER_SECRET",
            sanitize_multi_ai_error(error),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
