# -*- coding: utf-8 -*-
import asyncio
import html
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List, Optional

from config import SEARCH_CONFIG


class _DuckDuckGoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results: List[Dict[str, str]] = []
        self.current: Optional[Dict[str, str]] = None
        self.in_title = False
        self.in_snippet = False
        self.title_parts: List[str] = []
        self.snippet_parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "")

        if tag == "a" and "result__a" in class_name:
            href = attrs_dict.get("href", "")
            self.current = {"url": self._clean_duck_url(href)}
            self.title_parts = []
            self.snippet_parts = []
            self.in_title = True

        if self.current and tag in ("a", "div") and "result__snippet" in class_name:
            self.in_snippet = True

    def handle_endtag(self, tag):
        if tag == "a" and self.in_title:
            self.in_title = False

        if tag == "div" and self.in_snippet:
            self.in_snippet = False

        if self.current and tag == "div":
            self._flush_current()

    def handle_data(self, data):
        if self.current and self.in_title:
            self.title_parts.append(data)
        if self.current and self.in_snippet:
            self.snippet_parts.append(data)

    def close(self):
        self._flush_current()
        super().close()

    def _flush_current(self):
        if not self.current:
            return

        titulo = self._clean_text(" ".join(self.title_parts))
        snippet = self._clean_text(" ".join(self.snippet_parts))
        url = self.current.get("url", "")

        if titulo and url.startswith("http"):
            self.results.append({
                "titulo": titulo,
                "url": url,
                "snippet": snippet,
                "fonte": self._domain(url),
            })

        self.current = None
        self.title_parts = []
        self.snippet_parts = []
        self.in_title = False
        self.in_snippet = False

    @staticmethod
    def _clean_text(value: str) -> str:
        value = html.unescape(value or "")
        value = re.sub(r"\s+", " ", value).strip()
        return value

    @staticmethod
    def _domain(url: str) -> str:
        try:
            host = urllib.parse.urlparse(url).netloc.lower()
            return host.replace("www.", "")
        except Exception:
            return ""

    @staticmethod
    def _clean_duck_url(url: str) -> str:
        if not url:
            return ""

        url = html.unescape(url)

        if url.startswith("//duckduckgo.com/l/?"):
            url = "https:" + url

        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)

        if "uddg" in qs and qs["uddg"]:
            return urllib.parse.unquote(qs["uddg"][0])

        return url


class MotorBusca:
    def __init__(self, banco=None):
        self.banco = banco
        self.user_agent = SEARCH_CONFIG.get("user_agent", "HelpUS/1.0")
        self.timeout = float(SEARCH_CONFIG.get("timeout", 15.0))
        self.max_results = int(SEARCH_CONFIG.get("max_results", 5))

    async def buscar_web(self, consulta: str, limite: Optional[int] = None) -> List[Dict[str, str]]:
        limite = limite or self.max_results
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._buscar_web_sync, consulta, limite)

    def _buscar_web_sync(self, consulta: str, limite: int) -> List[Dict[str, str]]:
        consulta = (consulta or "").strip()
        if not consulta:
            return []

        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({
            "q": consulta,
            "kl": "br-pt",
        })

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except Exception:
            return []

        text = raw.decode("utf-8", errors="replace")

        parser = _DuckDuckGoParser()
        parser.feed(text)
        parser.close()

        return self._rank_and_dedupe(parser.results, limite)

    def _rank_and_dedupe(self, resultados: List[Dict[str, str]], limite: int) -> List[Dict[str, str]]:
        seen = set()
        limpos: List[Dict[str, str]] = []

        for item in resultados:
            url = item.get("url", "").strip()
            titulo = item.get("titulo", "").strip()
            snippet = item.get("snippet", "").strip()
            fonte = item.get("fonte", "").strip()

            if not url or not titulo:
                continue

            key = self._canonical_url(url)
            if key in seen:
                continue
            seen.add(key)

            limpos.append({
                "titulo": titulo[:180],
                "url": url,
                "snippet": snippet[:320],
                "fonte": fonte or "web",
            })

        def score(item: Dict[str, str]) -> int:
            fonte = item.get("fonte", "")
            url = item.get("url", "")
            s = 0

            if any(x in fonte for x in [".gov", ".edu", ".org"]):
                s += 20
            if any(x in fonte for x in ["reuters", "apnews", "bbc", "cnn", "nytimes", "theguardian", "folha", "estadao", "g1", "valor"]):
                s += 12
            if "wikipedia.org" in fonte:
                s -= 8
            if "facebook.com" in fonte or "instagram.com" in fonte or "tiktok.com" in fonte:
                s -= 10
            if len(url) < 140:
                s += 2

            return s

        limpos.sort(key=score, reverse=True)
        return limpos[:limite]

    @staticmethod
    def _canonical_url(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.rstrip("/")
        return f"{host}{path}"

    async def indexar_site(self, url: str, profundidade: int = 1) -> Dict[str, object]:
        if not self.banco:
            return {
                "url": url,
                "paginas_indexadas": 0,
                "status": "banco indisponivel",
            }

        conteudo = await self._baixar_texto(url)
        titulo = self._extrair_titulo(conteudo) or url
        await self.banco.indexar_pagina(url, titulo, conteudo)

        return {
            "url": url,
            "paginas_indexadas": 1,
            "status": "indexado",
        }

    async def _baixar_texto(self, url: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._baixar_texto_sync, url)

    def _baixar_texto_sync(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read(1_000_000)

        text = raw.decode("utf-8", errors="replace")
        text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _extrair_titulo(texto: str) -> str:
        if not texto:
            return ""
        return texto[:80].strip()
