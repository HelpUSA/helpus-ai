"""Script de Diagnostico e Reconciliacao Controlada de Sessoes Legadas (HelpUS AI - Ciclo 016).

Executa consultas analiticas em modo READ-ONLY para identificar:
1. Conflitos multi-usuario (distinct user_email > 1).
2. Mistura de mensagens anonimas (NULL/vazio) e autenticadas na mesma sessao.
3. Conflitos multi-projeto sob mesmo proprietario (distinct project_id > 1).
Gera relatorio detalhado para auditoria sem mutacao de dados.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("reconcile_sessoes_diagnostic")

def diagnosticar_sessoes_legadas(database_url: str) -> Dict[str, Any]:
    """Conecta ao PostgreSQL e diagnostica sessoes limpas vs confluentes em 3 categorias."""
    try:
        import psycopg
    except ImportError:
        logger.error("Driver 'psycopg' nao encontrado no ambiente.")
        return {"ok": False, "error": "psycopg missing"}

    report = {
        "ok": True,
        "database_url_configured": bool(database_url),
        "total_sessoes_legadas": 0,
        "sessoes_elegiveis_migracao_limpa": 0,
        "total_conflitos": 0,
        "conflitos_multi_usuario": [],
        "conflitos_mistura_anonimo": [],
        "conflitos_multi_projeto": [],
    }

    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                # 1. Total de sessoes unicas em conversas
                cur.execute("""
                    SELECT COUNT(DISTINCT session_id)
                    FROM conversas
                    WHERE session_id IS NOT NULL AND session_id != ''
                """)
                row = cur.fetchone()
                report["total_sessoes_legadas"] = row[0] if row else 0

                # 2. Conflitos multi-usuario (> 1 email distinto)
                cur.execute("""
                    SELECT 
                        session_id,
                        COUNT(DISTINCT LOWER(user_email)) AS num_owners,
                        ARRAY_AGG(DISTINCT LOWER(user_email)) AS emails,
                        COUNT(*) AS total_mensagens
                    FROM conversas
                    WHERE session_id IS NOT NULL AND session_id != ''
                    GROUP BY session_id
                    HAVING COUNT(DISTINCT LOWER(user_email)) > 1
                    ORDER BY total_mensagens DESC
                """)
                for r in cur.fetchall():
                    report["conflitos_multi_usuario"].append({
                        "session_id": r[0],
                        "distinct_owners": r[1],
                        "emails": r[2],
                        "message_count": r[3]
                    })

                # 3. Mistura de anonimo e autenticado na mesma sessao
                cur.execute("""
                    SELECT 
                        session_id,
                        COUNT(CASE WHEN user_email IS NULL OR TRIM(user_email) = '' THEN 1 END) AS msgs_anonimas,
                        COUNT(CASE WHEN user_email IS NOT NULL AND TRIM(user_email) != '' THEN 1 END) AS msgs_autenticadas,
                        ARRAY_AGG(DISTINCT LOWER(user_email)) FILTER (WHERE user_email IS NOT NULL AND TRIM(user_email) != '') AS emails
                    FROM conversas
                    WHERE session_id IS NOT NULL AND session_id != ''
                    GROUP BY session_id
                    HAVING COUNT(CASE WHEN user_email IS NULL OR TRIM(user_email) = '' THEN 1 END) > 0
                       AND COUNT(CASE WHEN user_email IS NOT NULL AND TRIM(user_email) != '' THEN 1 END) > 0
                """)
                for r in cur.fetchall():
                    report["conflitos_mistura_anonimo"].append({
                        "session_id": r[0],
                        "anonymous_messages": r[1],
                        "authenticated_messages": r[2],
                        "authenticated_emails": r[3]
                    })

                # 4. Multiplos projetos na mesma sessao (> 1 project_id)
                cur.execute("""
                    SELECT 
                        session_id,
                        LOWER(user_email) AS owner,
                        COUNT(DISTINCT COALESCE(project_id, 'general')) AS num_projetos,
                        ARRAY_AGG(DISTINCT COALESCE(project_id, 'general')) AS projetos
                    FROM conversas
                    WHERE session_id IS NOT NULL AND session_id != ''
                    GROUP BY session_id, LOWER(user_email)
                    HAVING COUNT(DISTINCT COALESCE(project_id, 'general')) > 1
                """)
                for r in cur.fetchall():
                    report["conflitos_multi_projeto"].append({
                        "session_id": r[0],
                        "owner": r[1],
                        "distinct_projects": r[2],
                        "projects": r[3]
                    })

                # Sessoes confluentes unicas
                conflicted_ids = set()
                for c in report["conflitos_multi_usuario"]:
                    conflicted_ids.add(c["session_id"])
                for c in report["conflitos_mistura_anonimo"]:
                    conflicted_ids.add(c["session_id"])
                for c in report["conflitos_multi_projeto"]:
                    conflicted_ids.add(c["session_id"])

                report["total_conflitos"] = len(conflicted_ids)
                report["sessoes_elegiveis_migracao_limpa"] = max(0, report["total_sessoes_legadas"] - len(conflicted_ids))

                logger.info(
                    f"Diagnostico concluido: {report['total_sessoes_legadas']} sessoes legadas. "
                    f"Elegiveis limpas: {report['sessoes_elegiveis_migracao_limpa']}, "
                    f"Conflitos totais isolados: {report['total_conflitos']}."
                )
                return report
    except Exception as e:
        logger.error(f"Erro ao executar diagnostico de sessoes: {e}")
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL nao configurada no ambiente. Modo simulado ou aguardando credencial de staging.")
        sys.exit(0)
    resultado = diagnosticar_sessoes_legadas(db_url)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
