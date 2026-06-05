# -*- coding: utf-8 -*-
from llama_cpp import Llama
import asyncio
from typing import List, Dict, Tuple
import time
from config import MODEL_PATH, MODEL_CONFIG, DEBUG

class CerebroIA:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or MODEL_PATH
        self.nome_modelo = "Mistral 7B"
        
        if DEBUG:
            print(f"Ã°Å¸Â§Â  Carregando modelo...")
        
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=MODEL_CONFIG["n_ctx"],
            n_threads=MODEL_CONFIG["n_threads"],
            n_batch=MODEL_CONFIG["n_batch"],
            verbose=False
        )
        
        if DEBUG:
            print("Ã¢Å“â€¦ Modelo carregado!")
    
    def _construir_prompt(self, pergunta: str, contexto_busca: str = "", historico: List[Dict] = None) -> str:
        system_prompt = "Voce e o HelpUS, um assistente virtual profissional em portugues do Brasil. Seu nome e HelpUS. Responda de forma clara, amigavel e objetiva. Sempre se apresente como HelpUS quando perguntado."
        
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        
        if historico:
            for msg in historico[-6:]:
                prompt += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
        
        if contexto_busca:
            pergunta = f"PERGUNTA: {pergunta}\n\nCONTEXTO DE PESQUISA:\n{contexto_busca}\n\nResponda com base no contexto."
        
        prompt += f"<|im_start|>user\n{pergunta}<|im_end|>\n<|im_start|>assistant\n"
        return prompt
    
    async def pensar(self, pergunta: str, contexto_busca: str = "", historico: List[Dict] = None, max_tokens: int = None) -> Tuple[str, int, float]:
        prompt = self._construir_prompt(pergunta, contexto_busca, historico)
        max_tokens = max_tokens or MODEL_CONFIG["max_tokens"]
        
        inicio = time.time()
        loop = asyncio.get_event_loop()
        
        def gerar():
            return self.llm(prompt, max_tokens=max_tokens, temperature=0.7, stop=["<|im_end|>"], echo=False)
        
        resultado = await loop.run_in_executor(None, gerar)
        resposta = resultado['choices'][0]['text'].strip()
        tokens = resultado['usage']['completion_tokens']
        tempo = round(time.time() - inicio, 2)
        
        return resposta, tokens, tempo