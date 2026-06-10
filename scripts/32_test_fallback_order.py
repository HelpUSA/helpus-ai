# -*- coding: utf-8 -*-
"""Unit-style tests for HelpUS AI provider fallback order.

This script uses in-process mocks and does not call external providers.
It validates that CerebroIA.pensar honors AI_PROVIDER_ORDER and records
last_provider_used / last_fallback_reason safely.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import cerebro  # noqa: E402


class FakeGeminiResponse:
    text = "gemini ok"


class FakeGeminiModels:
    def __init__(self, should_fail=True):
        self.should_fail = should_fail

    def generate_content(self, model, contents):
        if self.should_fail:
            raise RuntimeError("gemini mocked failure")
        return FakeGeminiResponse()


class FakeGeminiClient:
    def __init__(self, should_fail=True):
        self.models = FakeGeminiModels(should_fail=should_fail)


class FakeHTTPResponse:
    def __init__(self, provider, should_fail=False):
        self.provider = provider
        self.should_fail = should_fail

    def raise_for_status(self):
        if self.should_fail:
            raise RuntimeError(f"{self.provider} mocked failure")

    def json(self):
        return {
            "choices": [
                {"message": {"content": f"{self.provider} ok"}}
            ],
            "usage": {"completion_tokens": 7},
        }


class FakeAsyncClient:
    fail_openrouter = False
    calls = []

    def __init__(self, timeout=None):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        self.calls.append(str(url))
        if "openrouter" in str(url):
            return FakeHTTPResponse("openrouter", should_fail=self.fail_openrouter)
        return FakeHTTPResponse("deepseek", should_fail=False)


def make_brain(gemini_should_fail=True):
    brain = object.__new__(cerebro.CerebroIA)
    brain.provider = "gemini"
    brain.nome_modelo = "gemini-test"
    brain.client = FakeGeminiClient(should_fail=gemini_should_fail)
    return brain


async def run_case_openrouter_after_gemini_failure():
    cerebro.app_config.AI_PROVIDER_ORDER = ["gemini", "openrouter", "deepseek"]
    cerebro.app_config.OPENROUTER_API_KEY = "fake-openrouter"
    cerebro.app_config.DEEPSEEK_API_KEY = "fake-deepseek"
    cerebro.httpx.AsyncClient = FakeAsyncClient
    FakeAsyncClient.fail_openrouter = False
    FakeAsyncClient.calls = []

    brain = make_brain(gemini_should_fail=True)
    texto, tokens, _tempo = await brain.pensar("teste")

    assert texto == "openrouter ok"
    assert tokens == 7
    assert brain.last_provider_used == "openrouter"
    assert brain.last_fallback_reason == "gemini_failed"
    assert any("openrouter" in url for url in FakeAsyncClient.calls)


async def run_case_deepseek_after_two_failures():
    cerebro.app_config.AI_PROVIDER_ORDER = ["gemini", "openrouter", "deepseek"]
    cerebro.app_config.OPENROUTER_API_KEY = "fake-openrouter"
    cerebro.app_config.DEEPSEEK_API_KEY = "fake-deepseek"
    cerebro.httpx.AsyncClient = FakeAsyncClient
    FakeAsyncClient.fail_openrouter = True
    FakeAsyncClient.calls = []

    brain = make_brain(gemini_should_fail=True)
    texto, tokens, _tempo = await brain.pensar("teste")

    assert texto == "deepseek ok"
    assert tokens == 7
    assert brain.last_provider_used == "deepseek"
    assert brain.last_fallback_reason == "gemini_failed_openrouter_failed"
    assert any("openrouter" in url for url in FakeAsyncClient.calls)
    assert any("deepseek" in url for url in FakeAsyncClient.calls)


async def run_case_custom_order_openrouter_first():
    cerebro.app_config.AI_PROVIDER_ORDER = ["openrouter"]
    cerebro.app_config.OPENROUTER_API_KEY = "fake-openrouter"
    cerebro.httpx.AsyncClient = FakeAsyncClient
    FakeAsyncClient.fail_openrouter = False
    FakeAsyncClient.calls = []

    brain = make_brain(gemini_should_fail=False)
    texto, tokens, _tempo = await brain.pensar("teste")

    assert texto == "openrouter ok"
    assert tokens == 7
    assert brain.last_provider_used == "openrouter"
    assert brain.last_fallback_reason is None
    assert any("openrouter" in url for url in FakeAsyncClient.calls)


async def main():
    await run_case_openrouter_after_gemini_failure()
    await run_case_deepseek_after_two_failures()
    await run_case_custom_order_openrouter_first()
    print("HELPUS_FALLBACK_ORDER_UNIT_OK")


if __name__ == "__main__":
    asyncio.run(main())
