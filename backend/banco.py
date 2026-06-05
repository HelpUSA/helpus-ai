# -*- coding: utf-8 -*-
import asyncpg
from typing import List, Dict
from config import DATABASE_URL, DEBUG

class BancoDados:
    def __init__(self):
        self.pool = None
        
    async def conectar(self):
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            if DEBUG:
                print("✅ PostgreSQL conectado")
        except Exception as e:
            print(f"❌ Erro ao conectar no PostgreSQL: {e}")
            raise
    
    async def criar_tabelas(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversas_session 
                ON conversas(session_id, created_at DESC)
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS paginas_indexadas (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    titulo TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    data_indexacao TIMESTAMP DEFAULT NOW()
                )
            """)
    
    async def salvar_mensagem(self, session_id: str, role: str, content: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO conversas (session_id, role, content) VALUES ($1, $2, $3)",
                session_id, role, content
            )
    
    async def carregar_mensagens(self, session_id: str, limite: int = 20) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role, content FROM conversas WHERE session_id = $1 ORDER BY created_at DESC LIMIT $2",
                session_id, limite
            )
            return [{"role": r['role'], "content": r['content']} for r in reversed(rows)]
    
    async def apagar_conversa(self, session_id: str):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM conversas WHERE session_id = $1", session_id)
    
    async def indexar_pagina(self, url: str, titulo: str, conteudo: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO paginas_indexadas (url, titulo, conteudo) VALUES ($1, $2, $3)
                ON CONFLICT (url) DO UPDATE SET titulo = $2, conteudo = $3, data_indexacao = NOW()
            """, url, titulo, conteudo[:10000])
    
    async def buscar_paginas(self, consulta: str, limite: int = 5) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT url, titulo, substring(conteudo, 1, 200) as trecho FROM paginas_indexadas WHERE titulo ILIKE $1 OR conteudo ILIKE $1 LIMIT $2",
                f"%{consulta}%", limite
            )
            return [{"url": r['url'], "titulo": r['titulo'], "snippet": r['trecho']} for r in rows]
    
    async def contar_paginas(self) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM paginas_indexadas")