from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/page.tsx"
ORPHAN = ROOT / "frontend/src/components/chat/ChatSidebar.tsx"
PACKAGE = ROOT / "package.json"

CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
]:
    assert required.exists(), (
        f"missing required file: {required}"
    )

assert not ORPHAN.exists(), (
    "failed generated ChatSidebar artifact remained"
)

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
    "smoke:phase-ao-ui":
        "python scripts/65_smoke_chat_sidebar_navigation.py",
    "smoke:phase-ao":
        "npm run smoke:phase-ao-ui && npm run smoke:phase-an",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

aside_match = re.search(r"<aside[\s\S]*?</aside>", page)
assert aside_match is not None, "missing <aside> element in page.tsx"
aside = aside_match.group(0)

# Functional sidebar markers
for marker in [
    "Nova conversa",
    "Buscar conversas",
    "conversasFiltradas",
    "carregarHistorico(conv.session_id)",
    "apagarConversa(conv.session_id",
    "Abrir conversa",
    "Copiar link",
    "Renomear",
    "Excluir",
    "tituloExibidoConversa",
    "formatarDataConversa",
    "Painel Operacional",
]:
    assert marker.lower() in aside.lower(), (
        f"missing sidebar marker: {marker}"
    )

for marker in [
    "renomearConversaLocal",
    "copiarLinkConversaPorId",
    "activeConversationTitle",
    "project_id",
]:
    assert marker in page, (
        f"missing Phase AO page marker: {marker}"
    )

for forbidden_sidebar_marker in [
    "Novo projeto",
    "Chats recentes -",
    "<span>Projetos</span>",
    "Filtrar chats deste projeto",
]:
    assert forbidden_sidebar_marker not in aside, (
        "old project sidebar marker remained: "
        + forbidden_sidebar_marker
    )

assert "placeholder=\"Buscar conversas\"" in page, "chat search must exist"
assert page.count("limparChat") >= 1, "limparChat action binding required"
assert page.count("carregarHistorico") >= 1, "carregarHistorico action binding required"
assert page.count("apagarConversa") >= 1, "apagarConversa action binding required"

# Enforce zero dead code blocks
assert "false &&" not in page, "Dead code {false && (...)} is strictly forbidden"

for marker in [
    "Phase AO implementation contract",
    "smoke:phase-ao",
    "65_smoke_chat_sidebar_navigation.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Chat navigation after Phase AO",
    "smoke:phase-ao",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AO chat navigation",
    "smoke:phase-ao",
]:
    assert marker in status, marker

for marker in [
    "Phase AO chat navigation",
    "smoke:phase-ao",
]:
    assert marker in roadmap, marker

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
    "approved: true",
    "executed: true",
]:
    assert forbidden not in page, (
        f"forbidden marker found: {forbidden}"
    )

print("SMOKE_CHAT_SIDEBAR_NAVIGATION_OK")
