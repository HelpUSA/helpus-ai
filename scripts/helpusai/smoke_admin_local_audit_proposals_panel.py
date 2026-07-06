from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "admin" / "local" / "page.tsx"
text = PAGE.read_text(encoding="utf-8")
required_markers = [
    "/local/plan/proposals",
    "Propostas auditaveis",
    "Criar proposta auditavel sem executar",
    "Listar propostas auditaveis",
    "Resultado da proposta",
    "Lista de propostas",
    "proposal_only",
    "pending_human_review",
    "setProposalResult(proposal)",
]
missing = [marker for marker in required_markers if marker not in text]
if missing:
    raise SystemExit(f"missing markers: {missing}")
print("OK smoke_admin_local_audit_proposals_panel")
