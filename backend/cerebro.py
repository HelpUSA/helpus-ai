# -*- coding: utf-8 -*-
import asyncio
import time
import httpx
from typing import List, Dict, Tuple

import config as app_config
from config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MODEL_PATH,
    MODEL_CONFIG,
    DEBUG,
)


class CerebroIA:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.nome_modelo = self.provider

        if self.provider == "gemini":
            self.nome_modelo = GEMINI_MODEL
            if not GEMINI_API_KEY:
                raise RuntimeError("GEMINI_API_KEY nao configurada.")
            from google import genai
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            return

        if self.provider == "local":
            self.nome_modelo = "Local GGUF"
            from llama_cpp import Llama
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=MODEL_CONFIG["n_ctx"],
                n_threads=MODEL_CONFIG["n_threads"],
                n_batch=MODEL_CONFIG["n_batch"],
                verbose=False,
            )
            return

        raise RuntimeError(f"AI_PROVIDER invalido: {self.provider}")

    def _construir_prompt(self, pergunta: str, contexto_busca: str = "", historico: List[Dict] = None) -> str:
        partes = [
            "Voce e o HelpUS, um assistente virtual profissional em portugues do Brasil.",
            "Seu nome publico e HelpUS.",
            "Voce representa a HelpUS.",
            "Nunca diga que voce e Gemini, Google, OpenAI, ChatGPT ou outro provedor.",
            "Quando perguntarem quem voce e, responda que voce e o HelpUS, o assistente inteligente da HelpUS.",
            "Voce pode usar IA generativa para responder, mas nao deve se apresentar como o modelo base.",
            "Responda de forma clara, amigavel e objetiva.",
        ]

        if historico:
            partes.append("\nHistorico recente:")
            for msg in historico[-6:]:
                partes.append(f"{msg.get('role', 'user')}: {msg.get('content', '')}")

        if contexto_busca:
            partes.append("\nContexto de pesquisa:")
            partes.append(contexto_busca)

        partes.append("\nPergunta:")
        partes.append(pergunta)

        return "\n".join(partes)

    async def pensar(
        self,
        pergunta: str,
        contexto_busca: str = "",
        historico: List[Dict] = None,
        max_tokens: int = None,
    ) -> Tuple[str, int, float]:
        inicio = time.time()
        self.last_provider_used = self.provider
        self.last_fallback_reason = None
        prompt = self._construir_prompt(pergunta, contexto_busca, historico)
        max_tokens = max_tokens or MODEL_CONFIG["max_tokens"]

        if self.provider == "gemini":
            try:
                resposta = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=GEMINI_MODEL,
                    contents=prompt,
                )
                texto = (getattr(resposta, "text", "") or "").strip()
                tempo = round(time.time() - inicio, 2)
                self.last_provider_used = "gemini"
                self.last_fallback_reason = None
                return texto, 0, tempo
            except Exception:
                if DEBUG:
                    print("Gemini falhou; tentando OpenRouter fallback.")
                try:
                    if not app_config.OPENROUTER_API_KEY:
                        raise RuntimeError('OPENROUTER_API_KEY ausente')
                    payload = dict(model=app_config.OPENROUTER_MODEL, messages=[dict(role="user", content=prompt)], max_tokens=max_tokens, temperature=MODEL_CONFIG["temperature"])
                    headers = dict(Authorization="Bearer " + app_config.OPENROUTER_API_KEY)
                    async with httpx.AsyncClient(timeout=app_config.AI_REVIEW_TIMEOUT) as client:
                        resposta = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                        resposta.raise_for_status()
                        dados = resposta.json()
                        self.last_provider_used = "openrouter"
                        self.last_fallback_reason = "gemini_failed"
                except Exception:
                    if not app_config.DEEPSEEK_API_KEY:
                        raise RuntimeError('DEEPSEEK_API_KEY ausente')
                    payload = dict(model=app_config.DEEPSEEK_MODEL, messages=[dict(role="user", content=prompt)], max_tokens=max_tokens, temperature=MODEL_CONFIG["temperature"])
                    headers = dict(Authorization="Bearer " + app_config.DEEPSEEK_API_KEY)
                    async with httpx.AsyncClient(timeout=app_config.AI_REVIEW_TIMEOUT) as client:
                        resposta = await client.post(app_config.DEEPSEEK_API_URL, headers=headers, json=payload)
                        resposta.raise_for_status()
                        dados = resposta.json()
                        self.last_provider_used = "deepseek"
                        self.last_fallback_reason = "gemini_failed_openrouter_failed"
                texto = dados["choices"][0]["message"]["content"].strip()
                tokens = dados.get("usage", {}).get("completion_tokens", 0)
                tempo = round(time.time() - inicio, 2)
                return texto, tokens, tempo

        def gerar():
            return self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=MODEL_CONFIG["temperature"],
                stop=["<|im_end|>"],
                echo=False,
            )

        resultado = await asyncio.to_thread(gerar)
        texto = resultado["choices"][0]["text"].strip()
        self.last_provider_used = self.provider
        self.last_fallback_reason = None
        tokens = resultado.get("usage", {}).get("completion_tokens", 0)
        tempo = round(time.time() - inicio, 2)
        return texto, tokens, tempo
