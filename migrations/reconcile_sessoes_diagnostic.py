"""Script de Diagnostico e Reconciliacao Controlada de Sessoes Legadas (HelpUS AI).

Executa consultas analiticas em modo READ-ONLY para identificar conflitos multi-tenant
em sessoes legadas e gerar relatorio detalhado para os operadores.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("reconcile_sessoes_diagnostic")

def diagnosticar_sessoes_legadas(database_url: str) -> Dict[str, Any]:
    """Conecta ao PostgreSQL e diagnostica sessoes limpas vs confluentes."""
    try:
        import psycopg
    except ImportError:
        logger.error("Driver 'psycopg' nao encontrado no ambiente.")
        return {"ok": False, "error": "psycopg missing"}

    report = {
        "ok": True,
        "database_url_configured": bool(database_url),
        "total_sessoes_legadas": 0,
        "sessoes_limpas": 0,
        "sessoes_conflito": 0,
        "detalhes_conflitos": []
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

                # 2. Diagnostico de conflitos (sessoes com > 1 email distinto)
                cur.execute("""
                    SELECT 
                        session_id,
                        COUNT(DISTINCT LOWER(user_email)) AS num_owners,
                        ARRAY_AGG(DISTINCT LOWER(user_email)) AS emails,
                        COUNT(*) AS total_mensagens,
                        MIN(created_at) AS primeiro_registro,
                        MAX(created_at) AS ultimo_registro
                    FROM conversas
                    WHERE session_id IS NOT NULL AND session_id != ''
                    GROUP BY session_id
                    HAVING COUNT(DISTINCT LOWER(user_email)) > 1
                    ORDER BY total_mensagens DESC
                """)
                conflitos = cur.fetchall()
                report["sessoes_conflito"] = len(conflitos)
                report["sessoes_limpas"] = report["total_sessoes_legadas"] - len(conflitos)

                for c in conflitos:
                    report["detalhes_conflitos"].append({
                        "session_id": c[0],
                        "distinct_owners_count": c[1],
                        "emails": c[2],
                        "message_count": c[3],
                        "first_seen": c[4].isoformat() if hasattr(c[4], "isoformat") else str(c[4]),
                        "last_seen": c[5].isoformat() if hasattr(c[5], "isoformat") else str(c[5]),
                    })

                logger.info(
                    f"Diagnostico concluido: {report['total_sessoes_legadas']} sessoes legadas. "
                    f"Limpas: {report['sessoes_limpas']}, Conflitos: {report['sessoes_conflito']}."
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
