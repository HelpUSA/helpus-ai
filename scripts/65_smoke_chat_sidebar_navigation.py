
from pathlib import Path
import json

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

return_position = page.find(
    "  return ("
)

aside_start = page.find(
    "          <aside",
    return_position,
)

aside_end = page.find(
    "          </aside>",
    aside_start,
)

assert return_position >= 0
assert aside_start >= 0
assert aside_end > aside_start

aside = page[
    aside_start:aside_end
]

for marker in [
    "Conversas",
    "Nova conversa",
    "Buscar conversas",
    "Atualizar lista",
    "conversasFiltradas.map",
    "carregarHistorico(conv.session_id)",
    "apagarConversa(conv.session_id)",
    "Abrir conversa",
    "Copiar link",
    "Renomear",
    "Excluir",
    "chatMenuOpenId",
    "deleteConfirmId",
    "tituloExibidoConversa",
    "formatarDataConversa",
    "Nenhuma conversa salva ainda.",
    "Nenhuma conversa corresponde à busca.",
    "Entre com Google para carregar suas conversas.",
    "Painel operacional",
]:
    assert marker in aside, (
        f"missing sidebar marker: {marker}"
    )

for marker in [
    "helpus_chat_aliases_v1",
    "chatAliases",
    "setChatAliases",
    "renomearConversaLocal",
    "copiarLinkConversaPorId",
    "activeConversationTitle",
    "project_id: 'general'",
    "Atualizar conversas",
    "Copiar link atual",
    "max-w-[85vw]",
    "bg-[#171717]",
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

assert page.count(
    "placeholder=\"Buscar conversas\""
) == 1, (
    "chat search must exist exactly once"
)

assert page.count(
    "onClick={limparChat}"
) >= 1

assert page.count(
    "void carregarHistorico(conv.session_id)"
) >= 2

assert page.count(
    "void apagarConversa(conv.session_id)"
) == 1

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
