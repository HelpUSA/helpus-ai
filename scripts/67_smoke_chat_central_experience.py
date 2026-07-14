
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/page.tsx"
PACKAGE = ROOT / "package.json"

CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_66 = ROOT / "scripts/66_smoke_ci_phase_ao_chain.py"
SMOKE_65 = ROOT / "scripts/65_smoke_chat_sidebar_navigation.py"
SMOKE_MESSAGE = ROOT / "scripts/smoke_chat_message_nameerror.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_66,
    SMOKE_65,
    SMOKE_MESSAGE,
]:
    assert required.exists(), (
        f"missing required file: {required}"
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
    "smoke:phase-aq-ui":
        "python scripts/67_smoke_chat_central_experience.py",
    "smoke:phase-aq":
        "npm run smoke:phase-aq-ui && npm run smoke:phase-ap",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: "
        f"{actual!r}"
    )

for marker in [
    "STARTER_PROMPTS",
    "Como posso ajudar?",
    "messagesViewportRef",
    "messagesEndRef",
    "abortControllerRef",
    "lastSubmittedText",
    "chatError",
    "showScrollToBottom",
    "scrollToBottom",
    "requestAnimationFrame",
    "textarea.style.height",
    "submitMessage",
    "reenviarUltimaMensagem",
    "cancelarResposta",
    "signal: controller.signal",
    "A resposta foi interrompida.",
    "Tentar novamente",
    "Interromper",
    "Usar novamente",
    "Ir para o fim",
    "Pesquisar na web",
    "aria-pressed={pesquisarWeb}",
    "Pesquisa web ativada",
    "Shift+Enter",
    "Limpar mensagem",
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
    "Copiar link",
    "Renomear",
    "Excluir",
    "project_id: 'general'",
]:
    assert marker in page, (
        f"missing Phase AO compatibility marker: {marker}"
    )

assert page.count(
    "signal: controller.signal"
) == 1

assert page.count(
    "ref={messagesEndRef}"
) == 1

assert page.count(
    "aria-pressed={pesquisarWeb}"
) == 1

assert page.count(
    "void apagarConversa(conv.session_id)"
) == 1

for marker in [
    "Phase AQ implementation contract",
    "smoke:phase-aq",
    "67_smoke_chat_central_experience.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Central chat experience after Phase AQ",
    "smoke:phase-aq",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AQ central chat experience",
    "smoke:phase-aq",
]:
    assert marker in status, marker

for marker in [
    "Phase AQ central chat experience",
    "smoke:phase-aq",
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
        f"forbidden runtime marker found: {forbidden}"
    )

print("SMOKE_CHAT_CENTRAL_EXPERIENCE_OK")
