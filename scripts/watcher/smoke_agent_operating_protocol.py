from pathlib import Path

path = Path("docs/HELPUS_AGENT_OPERATING_PROTOCOL.md")
text = path.read_text(encoding="utf-8-sig")

required = [
    "HelpUS Agent Operating Protocol",
    "Repo: `D:/dev/ai`",
    "Branch padrao: `main`",
    "Rotina segura antes de qualquer alteracao",
    "Validacoes reais obrigatorias",
    "python scripts/watcher/smoke_operational_release.py",
    "python scripts/watcher/smoke_health_report.py",
    "npm --prefix frontend run build",
    "git diff --check",
    "Comandos destrutivos ou sensiveis",
    "Nunca fazer deploy automatico sem autorizacao explicita",
    "Quando parar",
    "Criterio de pronto",
]

missing = [item for item in required if item not in text]
if missing:
    raise AssertionError(f"Missing agent protocol markers: {missing}")

print("AGENT_OPERATING_PROTOCOL_SMOKE_OK")
