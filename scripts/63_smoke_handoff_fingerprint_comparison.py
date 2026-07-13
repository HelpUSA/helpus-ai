
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
HANDOFF = ROOT / "docs/ai/MULTI_AGENT_HANDOFF.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_62 = ROOT / "scripts/62_smoke_ci_phase_ak_chain.py"
SMOKE_61 = ROOT / "scripts/61_smoke_handoff_fingerprint.py"
SMOKE_60 = ROOT / "scripts/60_smoke_ci_phase_ai_chain.py"
SMOKE_59 = ROOT / "scripts/59_smoke_handoff_json_export.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_62,
    SMOKE_61,
    SMOKE_60,
    SMOKE_59,
]:
    assert required.exists(), f"missing required file: {required}"

page = PAGE.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

package = json.loads(
    PACKAGE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
)

capabilities = CAPABILITIES.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

handoff = HANDOFF.read_text(
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
    "smoke:phase-am-ui":
        "python scripts/63_smoke_handoff_fingerprint_comparison.py",
    "smoke:phase-am":
        "npm run smoke:phase-am-ui && npm run smoke:phase-al",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "handoffFingerprintExpected",
    "setHandoffFingerprintExpected",
    "handoffFingerprintComparison",
    "setHandoffFingerprintComparison",
    "compararFingerprintHandoff",
    "currentFingerprint",
    "expectedFingerprint",
    "/^sha256:[0-9a-f]{64}$/",
    "gere_o_fingerprint_atual_primeiro",
    "fingerprint_informado_invalido",
    "comparacao_exata",
    "comparacao_divergente",
    "Comparar fingerprint localmente",
    "Cole outro SHA-256",
    'placeholder="sha256:..."',
    "spellCheck={false}",
    "onClick={compararFingerprintHandoff}",
    "Comparar SHA-256",
    "Nenhuma comparacao foi executada nesta sessao.",
    "nao estabelece confianca",
    "decisao automatica de confianca",
    "smoke:phase-am",
    "smoke:phase-al",
]:
    assert marker in page, (
        f"missing Phase AM page marker: {marker}"
    )

for marker in [
    "Fingerprint local do handoff",
    "Gerar SHA-256",
    "Preview JSON auditavel",
    "Baixar .json",
    "Checklist de prontidao do handoff",
    "Baixar .txt",
    "Copiar handoff",
]:
    assert marker in page, (
        f"missing previous UI marker: {marker}"
    )

for marker in [
    "Phase AM implementation contract",
    "smoke:phase-am",
    "63_smoke_handoff_fingerprint_comparison.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Explicit fingerprint comparison after Phase AM",
    "smoke:phase-am",
]:
    assert marker in handoff, marker

for marker in [
    "Fingerprint comparison after Phase AM",
    "smoke:phase-am",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AM fingerprint comparison",
    "smoke:phase-am",
]:
    assert marker in status, marker

for marker in [
    "Phase AM fingerprint comparison",
    "smoke:phase-am",
]:
    assert marker in roadmap, marker

assert page.count(
    "onClick={compararFingerprintHandoff}"
) == 1, "comparison must require one explicit click"

assert page.count(
    "/^sha256:[0-9a-f]{64}$/"
) == 1, "comparison format validation must exist once"

assert page.count(
    "window.crypto.subtle.digest("
) == 1, "fingerprint generation contract changed"

assert page.count(
    "link.click()"
) == 1, "legacy TXT download contract changed"

assert "approved: true" not in page
assert "executed: true" not in page
assert '"approved": true' not in page
assert '"executed": true' not in page

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in page, (
        f"forbidden execution marker found: {forbidden}"
    )

print("SMOKE_HANDOFF_FINGERPRINT_COMPARISON_OK")
