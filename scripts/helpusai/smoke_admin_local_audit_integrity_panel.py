from pathlib import Path

PAGE = Path("frontend/src/app/admin/local/page.tsx")
text = PAGE.read_text(encoding="utf-8")

required = [
    "proposalIntegrity",
    "setProposalIntegrity",
    "verificarIntegridadePropostas",
    "/local/plan/proposals/verify",
    "Verificar integridade auditavel",
    "Resultado da integridade",
    "prettyJson(proposalIntegrity)",
]

missing = [marker for marker in required if marker not in text]
if missing:
    raise SystemExit("missing audit integrity UI markers: " + ", ".join(missing))

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    if forbidden in text:
        raise SystemExit("unsafe local UI endpoint marker found: " + forbidden)

print("OK smoke_admin_local_audit_integrity_panel")
