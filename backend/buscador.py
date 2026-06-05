# -*- coding: utf-8 -*-
import httpx
from bs4 import BeautifulSoup
import asyncio
from typing import List, Dict
from urllib.parse import quote
import re
from config import SEARCH_CONFIG, DEBUG

class MotorBusca:
    def __init__(self, banco):
        self.banco = banco
        self.user_agent = SEARCH_CONFIG["user_agent"]
        self.timeout = SEARCH_CONFIG["timeout"]
        self.max_results = SEARCH_CONFIG["max_results"]
        self.paginas_indexadas = 0
    
    async def buscar(self, consulta: str) -> List[Dict]:
        resultados = []
        
        try:
            resultados_indice = await self.banco.buscar_paginas(consulta, self.max_results)
            resultados.extend(resultados_indice)
        except:
            pass
        
        if len(resultados) < 3:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(consulta)}&format=json"
                    resp = await client.get(url, headers={"User-Agent": self.user_agent})
                    if resp.status_code == 200:
                        import json
                        data = resp.json()
                        for page in data.get('query', {}).get('search', [])[:3]:
                            resultados.append({
                                "titulo": page['title'],
                                "snippet": self._limpar_html(page.get('snippet', '')),
                                "url": f"https://pt.wikipedia.org/wiki/{quote(page['title'])}",
                                "fonte": "Wikipedia"
                            })
            except:
                pass
        
        return resultados[:self.max_results]
    
    async def indexar_site(self, url: str, profundidade: int = 2) -> int:
        return 0
    
    def _limpar_html(self, texto: str) -> str:
        return re.sub(r'<[^>]+>', '', texto).strip()