const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const backend = path.join(root, "backend");
const bancoPath = path.join(backend, "banco.py");
const mainPath = path.join(backend, "main.py");

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content.replace(/\r\n/g, "\n"), "utf8");
  console.log("[write]", file);
}

write(bancoPath, `# -*- coding: utf-8 -*-
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
                    CREATE INDEX IF NOT EXISTS idx_conversas_user_email
                    ON conversas(user_email)
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversas_user_session
                    ON conversas(user_email, session_id)
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
    ):
        if not self.pool:
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO conversas (session_id, role, content, user_email, title)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session_id, role, content, user_email, title)
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
                        COUNT(*) AS total_mensagens
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
`);

let main = fs.readFileSync(mainPath, "utf8");

main = main.replace(
  /await banco\.salvar_mensagem\(\s*session_id,\s*["']user["'],\s*request\.mensagem\s*\)/g,
  `await banco.salvar_mensagem(
            session_id,
            "user",
            request.mensagem,
            user_email=usuario["email"] if usuario else None,
            title=request.mensagem[:80],
        )`
);

main = main.replace(
  /await banco\.salvar_mensagem\(\s*session_id,\s*["']assistant["'],\s*resposta\s*\)/g,
  `await banco.salvar_mensagem(
            session_id,
            "assistant",
            resposta,
            user_email=usuario["email"] if usuario else None,
        )`
);

if (!main.includes('@app.get("/conversas")')) {
  const marker = '@app.get("/historico/{session_id}")';
  const endpoint = `
@app.get("/conversas")
async def listar_conversas(usuario = Depends(obter_usuario_google)):
    """Lista conversas do usuario autenticado"""
    if not usuario:
        raise HTTPException(status_code=401, detail="Login Google obrigatorio.")

    try:
        return {
            "conversas": await banco.listar_conversas_usuario(usuario["email"], limite=50)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


`;

  if (!main.includes(marker)) {
    throw new Error("Marker de historico nao encontrado em main.py");
  }

  main = main.replace(marker, endpoint + marker);
}

main = main.replace(
  'async def historico(session_id: str):',
  'async def historico(session_id: str, usuario = Depends(obter_usuario_google)):'
);

main = main.replace(
  /mensagens = await banco\.carregar_mensagens\(session_id,\s*limite=100\)/g,
  'mensagens = await banco.carregar_mensagens(session_id, limite=100, user_email=usuario["email"] if usuario else None)'
);

main = main.replace(
  'async def apagar_conversa(session_id: str):',
  'async def apagar_conversa(session_id: str, usuario = Depends(obter_usuario_google)):'
);

main = main.replace(
  /await banco\.apagar_conversa\(session_id\)/g,
  'await banco.apagar_conversa(session_id, user_email=usuario["email"] if usuario else None)'
);

write(mainPath, main);

console.log("[history] Backend user-scoped history updated");

cp.execFileSync("python -m py_compile config.py banco.py cerebro.py buscador.py auth.py main.py", {
  cwd: backend,
  stdio: "inherit",
  shell: true,
});

console.log("[history] Compile OK");
