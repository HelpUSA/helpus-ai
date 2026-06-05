param(
  [string]$ProjectRoot = "D:/dev/ai"
)

$ErrorActionPreference = "Stop"

function WriteFile($Path, $Lines) {
  $parent = Split-Path -Parent $Path
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  Set-Content -LiteralPath $Path -Value $Lines -Encoding utf8
}

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$backend = Join-Path $root "backend"

Write-Output "[psycopg] Updating requirements..."
$req = Join-Path $backend "requirements.txt"
$content = Get-Content -LiteralPath $req
$content = $content `
  -replace "asyncpg==0.29.0","psycopg[binary]>=3.2.0,<4.0.0" `
  -replace "asyncpg>=0.30.0,<1.0.0","psycopg[binary]>=3.2.0,<4.0.0" `
  -replace "httpx==0.26.0","httpx>=0.28.1,<1.0.0" `
  -replace "pydantic==2.5.3","pydantic>=2.9.0,<3.0.0"
Set-Content -LiteralPath $req -Value $content -Encoding utf8

Write-Output "[psycopg] Rewriting banco.py..."
WriteFile (Join-Path $backend "banco.py") @(
"# -*- coding: utf-8 -*-",
"from typing import List, Dict",
"from psycopg_pool import AsyncConnectionPool",
"from config import DATABASE_URL",
"",
"class BancoDados:",
"    def __init__(self):",
"        self.pool: AsyncConnectionPool | None = None",
"",
"    async def conectar(self):",
"        self.pool = AsyncConnectionPool(DATABASE_URL, open=False)",
"        await self.pool.open()",
"",
"    async def fechar(self):",
"        if self.pool:",
"            await self.pool.close()",
"",
"    async def criar_tabelas(self):",
"        if not self.pool:",
"            return",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute('''",
"                    CREATE TABLE IF NOT EXISTS conversas (",
"                        id SERIAL PRIMARY KEY,",
"                        session_id VARCHAR(255) NOT NULL,",
"                        role VARCHAR(50) NOT NULL,",
"                        content TEXT NOT NULL,",
"                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
"                    )",
"                ''')",
"                await cur.execute('''",
"                    CREATE TABLE IF NOT EXISTS paginas_indexadas (",
"                        id SERIAL PRIMARY KEY,",
"                        url TEXT UNIQUE NOT NULL,",
"                        titulo TEXT,",
"                        conteudo TEXT,",
"                        data_indexacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
"                    )",
"                ''')",
"                await conn.commit()",
"",
"    async def salvar_mensagem(self, session_id: str, role: str, content: str):",
"        if not self.pool:",
"            return",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute(",
"                    'INSERT INTO conversas (session_id, role, content) VALUES (%s, %s, %s)',",
"                    (session_id, role, content)",
"                )",
"                await conn.commit()",
"",
"    async def carregar_mensagens(self, session_id: str, limite: int = 20) -> List[Dict]:",
"        if not self.pool:",
"            return []",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute(",
"                    'SELECT role, content FROM conversas WHERE session_id = %s ORDER BY created_at DESC LIMIT %s',",
"                    (session_id, limite)",
"                )",
"                rows = await cur.fetchall()",
"                return [{'role': r[0], 'content': r[1]} for r in reversed(rows)]",
"",
"    async def apagar_conversa(self, session_id: str):",
"        if not self.pool:",
"            return",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute('DELETE FROM conversas WHERE session_id = %s', (session_id,))",
"                await conn.commit()",
"",
"    async def indexar_pagina(self, url: str, titulo: str, conteudo: str):",
"        if not self.pool:",
"            return",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute(",
"                    '''",
"                    INSERT INTO paginas_indexadas (url, titulo, conteudo)",
"                    VALUES (%s, %s, %s)",
"                    ON CONFLICT (url)",
"                    DO UPDATE SET titulo = EXCLUDED.titulo, conteudo = EXCLUDED.conteudo, data_indexacao = NOW()",
"                    ''',",
"                    (url, titulo, conteudo[:10000])",
"                )",
"                await conn.commit()",
"",
"    async def buscar_paginas(self, consulta: str, limite: int = 5) -> List[Dict]:",
"        if not self.pool:",
"            return []",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute(",
"                    'SELECT url, titulo, substring(conteudo, 1, 200) as trecho FROM paginas_indexadas WHERE titulo ILIKE %s OR conteudo ILIKE %s LIMIT %s',",
"                    (f'%{consulta}%', f'%{consulta}%', limite)",
"                )",
"                rows = await cur.fetchall()",
"                return [{'url': r[0], 'titulo': r[1], 'snippet': r[2]} for r in rows]",
"",
"    async def contar_paginas(self) -> int:",
"        if not self.pool:",
"            return 0",
"        async with self.pool.connection() as conn:",
"            async with conn.cursor() as cur:",
"                await cur.execute('SELECT COUNT(*) FROM paginas_indexadas')",
"                row = await cur.fetchone()",
"                return int(row[0]) if row else 0"
)

Write-Output "[psycopg] Compile check..."
python -m py_compile `
  (Join-Path $backend "config.py") `
  (Join-Path $backend "banco.py") `
  (Join-Path $backend "cerebro.py") `
  (Join-Path $backend "buscador.py") `
  (Join-Path $backend "main.py")

Write-Output "[psycopg] Done."
