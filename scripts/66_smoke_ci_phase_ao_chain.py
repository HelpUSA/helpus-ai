
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
PAGE = ROOT / "frontend/src/app/page.tsx"

CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_65 = ROOT / "scripts/65_smoke_chat_sidebar_navigation.py"
SMOKE_64 = ROOT / "scripts/64_smoke_ci_phase_am_chain.py"
SMOKE_MESSAGE = ROOT / "scripts/smoke_chat_message_nameerror.py"

for required in [
    WORKFLOW,
    PACKAGE,
    PAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_65,
    SMOKE_64,
    SMOKE_MESSAGE,
]:
    assert required.exists(), (
        f"missing required file: {required}"
    )

workflow = WORKFLOW.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

package = json.loads(
    PACKAGE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
)

page = PAGE.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

capabilities = CAPABILITIES.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

local_audit = LOCAL_AUDIT.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

status = STATUS.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

roadmap = ROADMAP.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

expected_scripts = {
    "smoke:phase-ap-ci":
        "python scripts/66_smoke_ci_phase_ao_chain.py",
    "smoke:phase-ap":
        "npm run smoke:phase-ap-ci && npm run smoke:phase-ao",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: "
        f"{actual!r}"
    )

for marker in [
    "name: Local audit safety",
    "permissions:",
    "contents: read",
    "Validate Phase AO chat navigation contract",
    "python scripts/66_smoke_ci_phase_ao_chain.py",
    "Run complete chat navigation smoke chain",
    "npm run smoke:phase-ao",
    "npm run smoke:phase-am",
]:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-ao-ui",
    "smoke:phase-ao",
    "smoke:phase-an",
    "smoke:phase-am",
    "smoke:phase-al",
    "smoke:phase-ak",
    "smoke:phase-ai",
    "smoke:phase-z",
    "smoke:local-audit-safety",
]:
    assert marker in package["scripts"], (
        f"missing smoke dependency: {marker}"
    )

for marker in [
    "Conversas",
    "Buscar conversas",
    "Atualizar lista",
    "conversasFiltradas.map",
    "void carregarHistorico(conv.session_id)",
    "void apagarConversa(conv.session_id)",
    "Abrir conversa",
    "Copiar link",
    "Renomear",
    "Excluir",
    "project_id: 'general'",
]:
    assert marker in page, (
        f"missing Phase AO page marker: {marker}"
    )

for marker in [
    "Phase AP implementation contract",
    "smoke:phase-ap",
    "66_smoke_ci_phase_ao_chain.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Phase AO CI chain after Phase AP",
    "smoke:phase-ap",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AP CI Phase AO chain",
    "smoke:phase-ap",
]:
    assert marker in status, marker

for marker in [
    "Phase AP CI Phase AO chain",
    "smoke:phase-ap",
]:
    assert marker in roadmap, marker

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in workflow, (
        f"forbidden workflow marker found: {forbidden}"
    )

print("SMOKE_CI_PHASE_AO_CHAIN_OK")
