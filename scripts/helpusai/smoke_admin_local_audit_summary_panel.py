from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
page = ROOT / "frontend" / "src" / "app" / "admin" / "local" / "page.tsx"
text = page.read_text(encoding="utf-8")

required = [
    "proposalSummary",
    "setProposalSummary",
    "carregarResumoPropostas",
    "Carregar resumo auditavel",
    "Resumo auditavel",
    "/local/plan/proposals/summary?limit=200",
    "JSON.stringify(proposalSummary, null, 2)",
]
missing = [marker for marker in required if marker not in text]
if missing:
    raise SystemExit("missing admin local summary UI markers: " + ", ".join(missing))

for forbidden in [
    "postLocal<unknown>('/local/plan/proposals/summary",
    "postLocal('/local/plan/proposals/summary",
    "fetchLocal<unknown>('/local/execute",
    "fetchLocal<unknown>('/local/commands",
    "fetchLocal<unknown>('/local/plan/execute",
    "fetchLocal<unknown>('/local/plan/run",
    "fetchLocal<unknown>('/local/plan/approve",
]:
    if forbidden in text:
        raise SystemExit("pain local summary UI unsafe marker found: " + forbidden)

print("OK smoke_admin_local_audit_summary_panel")
