
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

SMOKE_54 = ROOT / "scripts/54_smoke_ci_phase_ac_chain.py"
SMOKE_53 = ROOT / "scripts/53_smoke_handoff_copy_clipboard.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_54,
    SMOKE_53,
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
    "smoke:phase-ae-ui":
        "python scripts/55_smoke_handoff_download.py",
    "smoke:phase-ae":
        "npm run smoke:phase-ae-ui && npm run smoke:phase-ad",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "handoffDownloadStatus",
    "setHandoffDownloadStatus",
    "baixarResumoHandoff",
    "new Blob(",
    "text/plain;charset=utf-8",
    "URL.createObjectURL",
    "document.createElement('a')",
    "link.download = 'helpusai-handoff.txt'",
    "document.body.appendChild(link)",
    "link.click()",
    "link.remove()",
    "URL.revokeObjectURL",
    "Baixar .txt",
    "onClick={baixarResumoHandoff}",
    "Arquivo de handoff preparado localmente.",
    "Download indisponivel.",
    "arquivo de texto local",
    "smoke:phase-ae",
    "smoke:phase-ac",
]:
    assert marker in page, (
        f"missing Phase AE page marker: {marker}"
    )

for marker in [
    "Copiar handoff",
    "Resumo de handoff multiagente",
    "Modo de proposta de patch",
    "Matriz de risco estruturado",
    "Capacidades da IA",
]:
    assert marker in page, (
        f"missing previous UI marker: {marker}"
    )

for marker in [
    "Phase AE implementation contract",
    "smoke:phase-ae",
    "55_smoke_handoff_download.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Downloadable handoff after Phase AE",
    "smoke:phase-ae",
]:
    assert marker in handoff, marker

for marker in [
    "Handoff download after Phase AE",
    "smoke:phase-ae",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AE handoff download",
    "smoke:phase-ae",
]:
    assert marker in status, marker

for marker in [
    "Phase AE handoff download",
    "smoke:phase-ae",
]:
    assert marker in roadmap, marker

assert page.count(
    "onClick={baixarResumoHandoff}"
) == 1, "download must require exactly one explicit click"

assert page.count(
    "link.click()"
) == 1, "download trigger must exist exactly once"

print("SMOKE_HANDOFF_DOWNLOAD_OK")
