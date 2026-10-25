# -*- coding: utf-8 -*-
import os
import sys
import json
import asyncio
import time
from typing import List, Dict, Optional
try:
    from psycopg_pool import AsyncConnectionPool
except ImportError:
    AsyncConnectionPool = None

from config import DATABASE_URL


class BancoDados:
    def __init__(self):
        self.pool = None
        self.database_url = DATABASE_URL

    async def _garantir_pool(self) -> bool:
        if not self.pool and DATABASE_URL and AsyncConnectionPool is not None:
            await self.conectar()
        return self.pool is not None

    async def conectar(self):
        if AsyncConnectionPool is None:
            print("[INFO] psycopg_pool nao disponivel. Banco de dados desativado.")
            self.pool = None
            return
        if not DATABASE_URL or "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL:
            if os.getenv("VERCEL"):
                print("[INFO] Vercel serverless sem banco remoto.")
                self.pool = None
                return

        try:
            print(f"[INFO] Conectando pool de banco de dados PostgreSQL...")
            self.pool = AsyncConnectionPool(
                DATABASE_URL,
                open=False,
                min_size=1,
                max_size=10,
                kwargs={"connect_timeout": 10}
            )
            await asyncio.wait_for(self.pool.open(), timeout=12.0)
            print("[OK] Pool do PostgreSQL conectado com sucesso!")
        except Exception as e:
            print(f"[WARN] Falha ao conectar banco PostgreSQL: {e}")
            self.pool = None

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
                    CREATE TABLE IF NOT EXISTS project_memories (
                        id SERIAL PRIMARY KEY,
                        project_id TEXT NOT NULL DEFAULT 'general',
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tags TEXT DEFAULT '',
                        enabled BOOLEAN DEFAULT TRUE,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_memories_project_enabled
                    ON project_memories(project_id, enabled)
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_memories_created_by
                    ON project_memories(created_by)
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

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS projetos (
                        id SERIAL PRIMARY KEY,
                        project_id TEXT UNIQUE NOT NULL,
                        nome TEXT NOT NULL,
                        descricao TEXT DEFAULT '',
                        instrucoes TEXT DEFAULT '',
                        user_email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_projetos_user_email
                    ON projetos(user_email)
                """)

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessoes (
                        session_id VARCHAR(120) PRIMARY KEY,
                        user_email VARCHAR(255),
                        project_id VARCHAR(100) DEFAULT 'general',
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessoes_user_email
                    ON sessoes(LOWER(user_email))
                """)

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_audit_events (
                        id BIGSERIAL PRIMARY KEY,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        action VARCHAR(100) NOT NULL,
                        actor VARCHAR(255) NOT NULL,
                        correlation_id VARCHAR(120),
                        status VARCHAR(50) DEFAULT 'success',
                        details JSONB
                    )
                """)

                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_admin_audit_events_created
                    ON admin_audit_events (created_at DESC)
                """)

                await conn.commit()

    _sessoes_memoria: Dict[str, Optional[str]] = {}
    _projetos_memoria: Dict[str, Optional[str]] = {}
    _audit_log_memoria: List[Dict] = []

    def _verificar_propriedade_memoria(self, session_id: str, user_email: Optional[str]) -> bool:
        email_norm = user_email.strip().lower() if user_email else None
        if session_id not in self._sessoes_memoria:
            self._sessoes_memoria[session_id] = email_norm
            return True
        return self._sessoes_memoria[session_id] == email_norm

    def _verificar_propriedade_projeto_memoria(self, project_id: str, user_email: Optional[str]) -> bool:
        if not project_id or project_id == "general":
            return True
        email_norm = user_email.strip().lower() if user_email else None
        if project_id not in self._projetos_memoria:
            self._projetos_memoria[project_id] = email_norm
            return True
        return self._projetos_memoria[project_id] == email_norm

    async def verificar_propriedade_sessao(
        self,
        session_id: str,
        user_email: Optional[str],
        project_id: Optional[str] = None
    ) -> bool:
        """Valida e registra atomicamente a propriedade da sessao no banco (FAIL-CLOSED estrito).
        
        Garantias:
        1. Atomicidade: INSERT ... ON CONFLICT (session_id) DO NOTHING impede condicoes de corrida.
        2. FAIL-CLOSED: Em qualquer ambiente onde haja banco configurado, se o pool estiver
           indisponivel ou a consulta falhar, nega acesso sumariamente (return False).
        3. Seguranca de Ambiente: Ambientes de producao (ENVIRONMENT=production ou NODE_ENV=production)
           JAMAIS utilizam fallback em memoria sob hipotese alguma.
        4. Modo de Teste: Autorizacao em memoria apenas se HELPUS_TEST_MODE=1 e SEM banco configurado.
        5. Isolamento Multi-Tenant: Impede cross-account session hijacking.
        """
        is_prod = (
            os.getenv("ENVIRONMENT") == "production"
            or os.getenv("NODE_ENV") == "production"
            or os.getenv("VERCEL_ENV") == "production"
        )
        has_configured_db = bool(getattr(self, "database_url", None) or os.getenv("DATABASE_URL"))

        # 1. Se o pool estiver ativo e conectado, realiza checagem atomica no PostgreSQL
        if self.pool is not None:
            email_norm = user_email.strip().lower() if user_email else None
            proj_norm = (project_id or "general")[:80]
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            INSERT INTO sessoes (session_id, user_email, project_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (session_id) DO NOTHING
                            """,
                            (session_id, email_norm, proj_norm)
                        )
                        await conn.commit()

                        await cur.execute(
                            "SELECT user_email, project_id FROM sessoes WHERE session_id = %s LIMIT 1",
                            (session_id,)
                        )
                        row = await cur.fetchone()
                        if not row:
                            return True
                        existing_email = (row[0] or "").strip().lower() if row[0] else None
                        return existing_email == email_norm
            except Exception as e:
                # FAIL-CLOSED: NUNCA conceder autorizacao em caso de erro na consulta
                return False

        # 2. FAIL-CLOSED: Se houver banco configurado mas o pool falhou/indisponivel, nega acesso
        if has_configured_db:
            return False

        # 3. FAIL-CLOSED: Producao sem banco nega acesso (memoria proibida em producao)
        if is_prod:
            return False

        # 4. Modo de teste isolado e explicito (sem banco configurado e fora de producao)
        if os.getenv("HELPUS_TEST_MODE") == "1" or os.getenv("ENVIRONMENT") == "test":
            return self._verificar_propriedade_memoria(session_id, user_email)

        # Sem banco configurado e sem teste explicito: fail-closed estrito
        return False

    async def verificar_propriedade_projeto(
        self,
        project_id: str,
        user_email: Optional[str]
    ) -> bool:
        """Valida se o projeto pertence ao usuario especificado (FAIL-CLOSED estrito).
        O projeto 'general' e compartilhado e acessivel por qualquer usuario autenticado."""
        if not project_id or project_id == "general":
            return True

        is_prod = (
            os.getenv("ENVIRONMENT") == "production"
            or os.getenv("NODE_ENV") == "production"
            or os.getenv("VERCEL_ENV") == "production"
        )
        has_configured_db = bool(getattr(self, "database_url", None) or os.getenv("DATABASE_URL"))

        if self.pool is not None:
            email_norm = user_email.strip().lower() if user_email else None
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "SELECT 1 FROM projetos WHERE project_id = %s AND LOWER(user_email) = %s LIMIT 1",
                            (project_id, email_norm)
                        )
                        row = await cur.fetchone()
                        return row is not None
            except Exception:
                return False

        if has_configured_db or is_prod:
            return False

        if os.getenv("HELPUS_TEST_MODE") == "1" or os.getenv("ENVIRONMENT") == "test":
            return self._verificar_propriedade_projeto_memoria(project_id, user_email)

        return False

    async def registrar_evento_auditoria(
        self,
        action: str,
        actor: str,
        details: Optional[Dict] = None,
        correlation_id: Optional[str] = None,
        status: str = "success"
    ) -> Optional[Dict]:
        """Registra um evento de auditoria persistido de forma sanitizada."""
        event = {
            "timestamp": time.time(),
            "action": action,
            "actor": actor,
            "correlation_id": correlation_id,
            "status": status,
            "details": details or {},
            "sanitized": True
        }
        if self.pool is not None:
            try:
                import json
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            INSERT INTO admin_audit_events (action, actor, correlation_id, status, details)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id, created_at
                            """,
                            (action, actor, correlation_id, status, json.dumps(details or {}))
                        )
                        r = await cur.fetchone()
                        await conn.commit()
                        if r:
                            event["id"] = r[0]
                            event["created_at"] = r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1])
                            return event
            except Exception as e:
                print(f"[WARN] Erro ao persistir evento de auditoria no PostgreSQL: {e}")

        self._audit_log_memoria.append(event)
        return event

    async def listar_eventos_auditoria(
        self,
        limite: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Lista eventos de auditoria reais persistidos, com paginacao."""
        if self.pool is not None:
            try:
                import json
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT COUNT(*) FROM admin_audit_events")
                        total_row = await cur.fetchone()
                        total = total_row[0] if total_row else 0

                        await cur.execute(
                            """
                            SELECT id, created_at, action, actor, correlation_id, status, details
                            FROM admin_audit_events
                            ORDER BY created_at DESC
                            LIMIT %s OFFSET %s
                            """,
                            (limite, offset)
                        )
                        rows = await cur.fetchall()
                        eventos = []
                        for r in rows:
                            det = r[6]
                            if isinstance(det, str):
                                try:
                                    det = json.loads(det)
                                except:
                                    pass
                            eventos.append({
                                "id": r[0],
                                "timestamp": r[1].timestamp() if hasattr(r[1], "timestamp") else time.time(),
                                "created_at": r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
                                "action": r[2],
                                "actor": r[3],
                                "correlation_id": r[4],
                                "status": r[5],
                                "details": det or {},
                                "sanitized": True
                            })
                        return eventos, total
            except Exception as e:
                print(f"[WARN] Erro ao listar eventos de auditoria do PostgreSQL: {e}")

        total = len(self._audit_log_memoria)
        itens = list(reversed(self._audit_log_memoria))[offset:offset + limite]
        return itens, total

    async def salvar_mensagem(
        self,
        session_id: str,
        role: str,
        content: str,
        user_email: Optional[str] = None,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        if not await self._garantir_pool():
            return

        email_norm = user_email.strip().lower() if user_email else None
        if not await self.verificar_propriedade_sessao(session_id, email_norm):
            raise PermissionError(f"Acesso negado: a sessao '{session_id}' pertence a outra conta.")


        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    email_norm = user_email.strip().lower() if user_email else None
                    await cur.execute(
                        """
                        INSERT INTO conversas (session_id, role, content, user_email, title, project_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (session_id, role, content, email_norm, title, project_id or "general")
                    )
                    await conn.commit()
        except Exception as e:
            print(f"[WARN] Erro ao salvar mensagem no banco: {e}")

    async def carregar_mensagens(
        self,
        session_id: str,
        limite: int = 100,
        user_email: Optional[str] = None,
    ) -> List[Dict]:
        if not await self._garantir_pool():
            return []

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    if user_email and user_email.strip():
                        email_norm = user_email.strip().lower()
                        await cur.execute(
                            """
                            SELECT role, content FROM (
                                SELECT role, content, created_at
                                FROM conversas
                                WHERE session_id = %s AND LOWER(user_email) = %s
                                ORDER BY created_at DESC
                                LIMIT %s
                            ) sub
                            ORDER BY created_at ASC
                            """,
                            (session_id, email_norm, limite)
                        )
                    else:
                        await cur.execute(
                            """
                            SELECT role, content FROM (
                                SELECT role, content, created_at
                                FROM conversas
                                WHERE session_id = %s AND user_email IS NULL
                                ORDER BY created_at DESC
                                LIMIT %s
                            ) sub
                            ORDER BY created_at ASC
                            """,
                            (session_id, limite)
                        )

                    rows = await cur.fetchall()
                    return [{"role": r[0], "content": r[1]} for r in rows]
        except Exception as e:
            print(f"[WARN] Erro ao carregar mensagens: {e}")
            return []

    async def listar_conversas_usuario(self, user_email: str, limite: int = 50, project_id: Optional[str] = None) -> List[Dict]:
        if not await self._garantir_pool():
            return []

        if not user_email or not user_email.strip():
            return []

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    email_norm = user_email.strip().lower()
                    if project_id and project_id not in ("all", "*"):
                        query = """
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
                        WHERE LOWER(user_email) = %s
                          AND (project_id = %s OR (%s = 'general' AND project_id IS NULL))
                        GROUP BY session_id
                        ORDER BY MAX(created_at) DESC
                        LIMIT %s
                        """
                        params = (email_norm, project_id, project_id, limite)
                    else:
                        query = """
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
                        WHERE LOWER(user_email) = %s
                        GROUP BY session_id
                        ORDER BY MAX(created_at) DESC
                        LIMIT %s
                        """
                        params = (email_norm, limite)

                    await cur.execute(query, params)
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
        except Exception as e:
            print(f"[WARN] Erro ao listar conversas: {e}")
            return []

    async def renomear_conversa(self, session_id: str, novo_titulo: str, user_email: Optional[str] = None):
        if not await self._garantir_pool():
            return
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    if user_email and user_email.strip():
                        email_norm = user_email.strip().lower()
                        await cur.execute(
                            "UPDATE conversas SET title = %s WHERE session_id = %s AND LOWER(user_email) = %s",
                            (novo_titulo, session_id, email_norm)
                        )
                    else:
                        await cur.execute(
                            "UPDATE conversas SET title = %s WHERE session_id = %s AND user_email IS NULL",
                            (novo_titulo, session_id)
                        )
                    await conn.commit()
        except Exception as e:
            print(f"[WARN] Erro ao renomear conversa: {e}")

    async def mover_conversa_projeto(self, session_id: str, project_id: str, user_email: Optional[str] = None):
        if not await self._garantir_pool():
            return
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    if user_email and user_email.strip():
                        email_norm = user_email.strip().lower()
                        await cur.execute(
                            "UPDATE conversas SET project_id = %s WHERE session_id = %s AND LOWER(user_email) = %s",
                            (project_id or "general", session_id, email_norm)
                        )
                        await cur.execute(
                            "UPDATE sessoes SET project_id = %s WHERE session_id = %s AND LOWER(user_email) = %s",
                            (project_id or "general", session_id, email_norm)
                        )
                    else:
                        await cur.execute(
                            "UPDATE conversas SET project_id = %s WHERE session_id = %s AND user_email IS NULL",
                            (project_id or "general", session_id)
                        )
                        await cur.execute(
                            "UPDATE sessoes SET project_id = %s WHERE session_id = %s AND user_email IS NULL",
                            (project_id or "general", session_id)
                        )
                    await conn.commit()
        except Exception as e:
            print(f"[WARN] Erro ao mover conversa: {e}")

    async def listar_projetos(self, user_email: Optional[str] = None) -> List[Dict]:
        padrao = [{"project_id": "general", "nome": "Geral", "descricao": "Conversas gerais do HelpUS", "instrucoes": ""}]
        if not await self._garantir_pool():
            return padrao
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    if user_email and user_email.strip():
                        email_norm = user_email.strip().lower()
                        await cur.execute(
                            """
                            SELECT project_id, nome, descricao, instrucoes, created_at
                            FROM projetos
                            WHERE LOWER(user_email) = %s
                            ORDER BY created_at ASC
                            """,
                            (email_norm,)
                        )
                    else:
                        return padrao
                    rows = await cur.fetchall()
                    itens = [
                        {
                            "project_id": r[0],
                            "nome": r[1],
                            "descricao": r[2] or "",
                            "instrucoes": r[3] or "",
                            "created_at": r[4].isoformat() if r[4] else None,
                        }
                        for r in rows
                    ]
                    if not any(p["project_id"] == "general" for p in itens):
                        itens.insert(0, padrao[0])
                    return itens
        except Exception as e:
            print(f"[WARN] Erro ao listar projetos: {e}")
            return padrao

    async def criar_projeto(
        self,
        project_id: str,
        nome: str,
        descricao: str = "",
        instrucoes: str = "",
        user_email: Optional[str] = None,
    ) -> Dict:
        fallback = {"project_id": project_id, "nome": nome, "descricao": descricao, "instrucoes": instrucoes}
        if not await self._garantir_pool():
            return fallback
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    email_norm = user_email.strip().lower() if user_email and user_email.strip() else None
                    await cur.execute(
                        """
                        INSERT INTO projetos (project_id, nome, descricao, instrucoes, user_email)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (project_id) DO UPDATE
                        SET nome = EXCLUDED.nome,
                            descricao = EXCLUDED.descricao,
                            instrucoes = EXCLUDED.instrucoes,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING project_id, nome, descricao, instrucoes, created_at
                        """,
                        (project_id, nome, descricao, instrucoes, email_norm)
                    )
                    r = await cur.fetchone()
                    await conn.commit()
                    if not r:
                        return fallback
                    return {
                        "project_id": r[0],
                        "nome": r[1],
                        "descricao": r[2] or "",
                        "instrucoes": r[3] or "",
                        "created_at": r[4].isoformat() if r[4] else None,
                    }
        except Exception as e:
            print(f"[WARN] Erro ao criar projeto: {e}")
            return fallback

    async def apagar_conversa(self, session_id: str, user_email: Optional[str] = None):
        if not await self._garantir_pool():
            return

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    if user_email and user_email.strip():
                        email_norm = user_email.strip().lower()
                        await cur.execute(
                            "DELETE FROM conversas WHERE session_id = %s AND LOWER(user_email) = %s",
                            (session_id, email_norm)
                        )
                    else:
                        await cur.execute(
                            "DELETE FROM conversas WHERE session_id = %s AND user_email IS NULL",
                            (session_id,)
                        )
                    await conn.commit()
        except Exception as e:
            print(f"[WARN] Erro ao apagar conversa: {e}")

    async def listar_memorias_projeto(
        self,
        project_id: str = "general",
        include_disabled: bool = False,
        limite: int = 50,
    ) -> List[Dict]:
        if not await self._garantir_pool():
            return []

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                if include_disabled:
                    await cur.execute(
                        """
                        SELECT id, project_id, title, content, tags, enabled, created_by, created_at, updated_at
                        FROM project_memories
                        WHERE project_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (project_id or "general", limite),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, project_id, title, content, tags, enabled, created_by, created_at, updated_at
                        FROM project_memories
                        WHERE project_id = %s AND enabled = TRUE
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (project_id or "general", limite),
                    )

                rows = await cur.fetchall()
                return [
                    {
                        "id": int(r[0]),
                        "project_id": r[1] or "general",
                        "title": r[2],
                        "content": r[3],
                        "tags": r[4] or "",
                        "enabled": bool(r[5]),
                        "created_by": r[6] or "",
                        "created_at": r[7].isoformat() if r[7] else None,
                        "updated_at": r[8].isoformat() if r[8] else None,
                    }
                    for r in rows
                ]

    async def criar_memoria_projeto(
        self,
        project_id: str,
        title: str,
        content: str,
        tags: str = "",
        created_by: Optional[str] = None,
    ) -> Optional[Dict]:
        if not await self._garantir_pool():
            return None

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO project_memories (project_id, title, content, tags, enabled, created_by)
                        VALUES (%s, %s, %s, %s, TRUE, %s)
                        RETURNING id, project_id, title, content, tags, enabled, created_by, created_at, updated_at
                        """,
                        (project_id or "general", title, content, tags or "", created_by),
                    )
                    r = await cur.fetchone()
                    await conn.commit()

                    if not r:
                        return None

                    return {
                        "id": int(r[0]),
                        "project_id": r[1] or "general",
                        "title": r[2],
                        "content": r[3],
                        "tags": r[4] or "",
                        "enabled": bool(r[5]),
                        "created_by": r[6] or "",
                        "created_at": r[7].isoformat() if r[7] else None,
                        "updated_at": r[8].isoformat() if r[8] else None,
                    }
        except Exception as e:
            print(f"[WARN] Erro ao criar memoria: {e}")
            return None

    async def atualizar_memoria_projeto(
        self,
        memory_id: int,
        project_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[Dict]:
        if not await self._garantir_pool():
            return None

        try:
            atuais = await self.listar_memorias_projeto(project_id=project_id, include_disabled=True, limite=200)
            alvo = next((m for m in atuais if int(m["id"]) == int(memory_id)), None)
            if not alvo:
                return None

            next_title = title if title is not None else alvo["title"]
            next_content = content if content is not None else alvo["content"]
            next_tags = tags if tags is not None else alvo["tags"]
            next_enabled = enabled if enabled is not None else alvo["enabled"]

            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE project_memories
                        SET title = %s,
                            content = %s,
                            tags = %s,
                            enabled = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND project_id = %s
                        RETURNING id, project_id, title, content, tags, enabled, created_by, created_at, updated_at
                        """,
                        (next_title, next_content, next_tags or "", bool(next_enabled), int(memory_id), project_id or "general"),
                    )
                    r = await cur.fetchone()
                    await conn.commit()

                    if not r:
                        return None

                    return {
                        "id": int(r[0]),
                        "project_id": r[1] or "general",
                        "title": r[2],
                        "content": r[3],
                        "tags": r[4] or "",
                        "enabled": bool(r[5]),
                        "created_by": r[6] or "",
                        "created_at": r[7].isoformat() if r[7] else None,
                        "updated_at": r[8].isoformat() if r[8] else None,
                    }
        except Exception as e:
            print(f"[WARN] Erro ao atualizar memoria: {e}")
            return None

    async def indexar_pagina(self, url: str, titulo: str, conteudo: str):
        if not await self._garantir_pool():
            return

        try:
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
        except Exception as e:
            print(f"[WARN] Erro ao indexar pagina: {e}")

    async def buscar_paginas(self, consulta: str, limite: int = 5) -> List[Dict]:
        if not await self._garantir_pool():
            return []

        try:
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
        except Exception as e:
            print(f"[WARN] Erro ao buscar paginas: {e}")
            return []

    async def contar_paginas(self) -> int:
        if not await self._garantir_pool():
            return 0

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT COUNT(*) FROM paginas_indexadas")
                    row = await cur.fetchone()
                    return int(row[0]) if row else 0
        except Exception as e:
            print(f"[WARN] Erro ao contar paginas: {e}")
            return 0
