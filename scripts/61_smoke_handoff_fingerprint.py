
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

SMOKE_60 = ROOT / "scripts/60_smoke_ci_phase_ai_chain.py"
SMOKE_59 = ROOT / "scripts/59_smoke_handoff_json_export.py"
SMOKE_58 = ROOT / "scripts/58_smoke_ci_phase_ag_chain.py"
SMOKE_57 = ROOT / "scripts/57_smoke_handoff_readiness_checklist.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_60,
    SMOKE_59,
    SMOKE_58,
    SMOKE_57,
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
    "smoke:phase-ak-ui":
        "python scripts/61_smoke_handoff_fingerprint.py",
    "smoke:phase-ak":
        "npm run smoke:phase-ak-ui && npm run smoke:phase-aj",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "handoffFingerprint",
    "setHandoffFingerprint",
    "handoffFingerprintStatus",
    "setHandoffFingerprintStatus",
    "gerarFingerprintHandoff",
    "window.crypto?.subtle",
    "web_crypto_unavailable",
    "new TextEncoder()",
    "window.crypto.subtle.digest(",
    "'SHA-256'",
    "new Uint8Array(digest)",
    "byte.toString(16).padStart(2, '0')",
    "`sha256:${hexadecimal}`",
    "Fingerprint SHA-256 gerado localmente.",
    "Fingerprint indisponivel neste navegador.",
    "Fingerprint local do handoff",
    "Gerar SHA-256",
    "onClick={() => void gerarFingerprintHandoff()}",
    "Nenhum fingerprint foi gerado nesta sessao.",
    "nao e assinatura digital",
    "nao funciona como assinatura ou aprovacao",
    "smoke:phase-ak",
    "smoke:phase-aj",
]:
    assert marker in page, (
        f"missing Phase AK page marker: {marker}"
    )

for marker in [
    "Preview JSON auditavel",
    "Baixar .json",
    "Checklist de prontidao do handoff",
    "Baixar .txt",
    "Copiar handoff",
    "Resumo de handoff multiagente",
]:
    assert marker in page, (
        f"missing previous UI marker: {marker}"
    )

for marker in [
    "Phase AK implementation contract",
    "smoke:phase-ak",
    "61_smoke_handoff_fingerprint.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Local fingerprint after Phase AK",
    "smoke:phase-ak",
]:
    assert marker in handoff, marker

for marker in [
    "Handoff fingerprint after Phase AK",
    "smoke:phase-ak",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AK handoff fingerprint",
    "smoke:phase-ak",
]:
    assert marker in status, marker

for marker in [
    "Phase AK handoff fingerprint",
    "smoke:phase-ak",
]:
    assert marker in roadmap, marker

assert page.count(
    "onClick={() => void gerarFingerprintHandoff()}"
) == 1, "fingerprint must require exactly one explicit click"

assert page.count(
    "window.crypto.subtle.digest("
) == 1, "SHA-256 digest must be generated exactly once"

assert page.count(
    "link.click()"
) == 1, "legacy TXT download contract must remain unchanged"

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

print("SMOKE_HANDOFF_FINGERPRINT_OK")
