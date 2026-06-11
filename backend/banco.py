# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
from psycopg_pool import AsyncConnectionPool
from config import DATABASE_URL


class BancoDados:
    def __init__(self):
        self.pool: AsyncConnectionPool | None = None

    async def conectar(self):
        self.pool = AsyncConnectionPool(DATABASE_URL, open=False)
        await self.pool.open()

    async def fechar(self):
        if self.pool:
            await self.pool.close()

    async def criar_tabelas(self):
        if not self.pool:
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversas (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await cur.execute("""
                    ALTER TABLE conversas
                    ADD COLUMN IF NOT EXISTS user_email TEXT
                """)

                await cur.execute("""
                    ALTER TABLE conversas
                    ADD COLUMN IF NOT EXISTS title TEXT
                """)

                await cur.execute("""
                    ALTER TABLE conversas
                    ADD COLUMN IF NOT EXISTS project_id TEXT DEFAULT 'general'
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversas_user_email
                    ON conversas(user_email)
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversas_user_session
                    ON conversas(user_email, session_id)
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversas_user_project
                    ON conversas(user_email, project_id)
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversas_created_at
                    ON conversas(created_at)
                """)

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS paginas_indexadas (
                        id SERIAL PRIMARY KEY,
                        url TEXT UNIQUE NOT NULL,
                        titulo TEXT,
                        conteudo TEXT,
                        data_indexacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await conn.commit()

    async def salvar_mensagem(
        self,
        session_id: str,
        role: str,
        content: str,
        user_email: Optional[str] = None,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        if not self.pool:
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO conversas (session_id, role, content, user_email, title, project_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, role, content, user_email, title, project_id or "general")
                )
                await conn.commit()

    async def carregar_mensagens(
        self,
        session_id: str,
        limite: int = 20,
        user_email: Optional[str] = None,
    ) -> List[Dict]:
        if not self.pool:
            return []

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                if user_email:
                    await cur.execute(
                        """
                        SELECT role, content
                        FROM conversas
                        WHERE session_id = %s AND user_email = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (session_id, user_email, limite)
                    )
                else:
                    await cur.execute(
                        """
                        SELECT role, content
                        FROM conversas
                        WHERE session_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (session_id, limite)
                    )

                rows = await cur.fetchall()
                return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    async def listar_conversas_usuario(self, user_email: str, limite: int = 50) -> List[Dict]:
        if not self.pool:
            return []

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        session_id,
                        COALESCE(
                            NULLIF(MAX(title), ''),
                            LEFT((ARRAY_AGG(content ORDER BY created_at ASC))[1], 80),
                            'Nova conversa'
                        ) AS titulo,
                        MAX(created_at) AS updated_at,
                        COUNT(*) AS total_mensagens,
                        COALESCE(NULLIF(MAX(project_id), ''), 'general') AS project_id
                    FROM conversas
                    WHERE user_email = %s
                    GROUP BY session_id
                    ORDER BY MAX(created_at) DESC
                    LIMIT %s
                    """,
                    (user_email, limite)
                )

                rows = await cur.fetchall()
                return [
                    {
                        "session_id": r[0],
                        "titulo": r[1],
                        "updated_at": r[2].isoformat() if r[2] else None,
                        "total_mensagens": int(r[3] or 0),
                        "project_id": r[4] or "general",
                    }
                    for r in rows
                ]

    async def apagar_conversa(self, session_id: str, user_email: Optional[str] = None):
        if not self.pool:
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                if user_email:
                    await cur.execute(
                        "DELETE FROM conversas WHERE session_id = %s AND user_email = %s",
                        (session_id, user_email)
                    )
                else:
                    await cur.execute(
                        "DELETE FROM conversas WHERE session_id = %s",
                        (session_id,)
                    )
                await conn.commit()

    async def indexar_pagina(self, url: str, titulo: str, conteudo: str):
        if not self.pool:
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO paginas_indexadas (url, titulo, conteudo)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (url)
                    DO UPDATE SET
                        titulo = EXCLUDED.titulo,
                        conteudo = EXCLUDED.conteudo,
                        data_indexacao = NOW()
                    """,
                    (url, titulo, conteudo[:10000])
                )
                await conn.commit()

    async def buscar_paginas(self, consulta: str, limite: int = 5) -> List[Dict]:
        if not self.pool:
            return []

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT url, titulo, substring(conteudo, 1, 200) as trecho
                    FROM paginas_indexadas
                    WHERE titulo ILIKE %s OR conteudo ILIKE %s
                    LIMIT %s
                    """,
                    (f"%{consulta}%", f"%{consulta}%", limite)
                )
                rows = await cur.fetchall()
                return [{"url": r[0], "titulo": r[1], "snippet": r[2]} for r in rows]

    async def contar_paginas(self) -> int:
        if not self.pool:
            return 0

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM paginas_indexadas")
                row = await cur.fetchone()
                return int(row[0]) if row else 0
