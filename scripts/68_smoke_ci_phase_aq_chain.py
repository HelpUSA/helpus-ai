
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

SMOKE_67 = ROOT / "scripts/67_smoke_chat_central_experience.py"
SMOKE_66 = ROOT / "scripts/66_smoke_ci_phase_ao_chain.py"
SMOKE_65 = ROOT / "scripts/65_smoke_chat_sidebar_navigation.py"
SMOKE_MESSAGE = ROOT / "scripts/smoke_chat_message_nameerror.py"

for required in [
    WORKFLOW,
    PACKAGE,
    PAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_67,
    SMOKE_66,
    SMOKE_65,
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
    "smoke:phase-ar-ci":
        "python scripts/68_smoke_ci_phase_aq_chain.py",
    "smoke:phase-ar":
        "npm run smoke:phase-ar-ci && npm run smoke:phase-aq",
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
    "Validate Phase AQ central chat contract",
    "python scripts/68_smoke_ci_phase_aq_chain.py",
    "Run complete central chat smoke chain",
    "npm run smoke:phase-aq",
    "npm run smoke:phase-ao",
]:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-aq-ui",
    "smoke:phase-aq",
    "smoke:phase-ap",
    "smoke:phase-ao",
    "smoke:phase-an",
    "smoke:phase-am",
    "smoke:local-audit-safety",
]:
    assert marker in package["scripts"], (
        f"missing smoke dependency: {marker}"
    )

for marker in [
    "STARTER_PROMPTS",
    "messagesViewportRef",
    "messagesEndRef",
    "abortControllerRef",
    "signal: controller.signal",
    "reenviarUltimaMensagem",
    "cancelarResposta",
    "A resposta foi interrompida.",
    "Tentar novamente",
    "Ir para o fim",
    "Pesquisar na web",
    "aria-pressed={pesquisarWeb}",
]:
    assert marker in page, (
        f"missing Phase AQ page marker: {marker}"
    )

for marker in [
    "Conversas",
    "Buscar conversas",
    "Atualizar lista",
    "conversasFiltradas.map",
    "void carregarHistorico(conv.session_id)",
    "void apagarConversa(conv.session_id)",
]:
    assert marker in page, (
        f"missing Phase AO compatibility marker: {marker}"
    )

for marker in [
    "Phase AR implementation contract",
    "smoke:phase-ar",
    "68_smoke_ci_phase_aq_chain.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Phase AQ CI chain after Phase AR",
    "smoke:phase-ar",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AR CI Phase AQ chain",
    "smoke:phase-ar",
]:
    assert marker in status, marker

for marker in [
    "Phase AR CI Phase AQ chain",
    "smoke:phase-ar",
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

print("SMOKE_CI_PHASE_AQ_CHAIN_OK")
