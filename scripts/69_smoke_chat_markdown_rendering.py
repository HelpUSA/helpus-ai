
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/page.tsx"

MARKDOWN_COMPONENT = (
    ROOT
    / "frontend/src/app/markdown-message.tsx"
)

FRONTEND_PACKAGE = (
    ROOT
    / "frontend/package.json"
)

ROOT_PACKAGE = ROOT / "package.json"

CAPABILITIES = (
    ROOT
    / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
)

LOCAL_AUDIT = (
    ROOT
    / "docs/local-plan-audit.md"
)

ROADMAP = (
    ROOT
    / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"
)

STATUS = (
    ROOT
    / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
)


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
    )


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


page = read_text(PAGE)
component = read_text(MARKDOWN_COMPONENT)

for marker in (
    "type MessageSource",
    "<MarkdownMessage content={msg.content} />",
    "<SafeSourceLink",
    "key={`${fonte.url}-${i}`}",
    "msg.role === 'assistant'",
    "v0.34.0-dev",
    "const STARTER_PROMPTS = [",
    "function tituloConversa",
):
    require(
        marker in page,
        f"Missing page marker: {marker}",
    )

for marker in (
    "function renderInlineMarkdown",
    "function renderMessageContent",
    "dangerouslySetInnerHTML",
    "href={fonte.url}",
):
    require(
        marker not in page,
        f"Forbidden page marker: {marker}",
    )

for marker in (
    "import ReactMarkdown from 'react-markdown'",
    "import remarkGfm from 'remark-gfm'",
    "export function normalizeHttpUrl(",
    "export function SafeSourceLink({",
    "export function MarkdownMessage({",
    "<ReactMarkdown",
    "remarkPlugins={[remarkGfm]}",
    "skipHtml",
    "urlTransform={normalizeHttpUrl}",
    "Copiar código",
    'rel="noopener noreferrer nofollow"',
    "parsed.protocol !== 'http:'",
    "parsed.protocol !== 'https:'",
    "[Imagem bloqueada]",
):
    require(
        marker in component,
        f"Missing component marker: {marker}",
    )

require(
    "dangerouslySetInnerHTML"
    not in component,
    "Raw HTML rendering marker found.",
)

frontend_package = json.loads(
    read_text(FRONTEND_PACKAGE)
)

frontend_dependencies = (
    frontend_package.get(
        "dependencies",
        {},
    )
)

require(
    "react-markdown"
    in frontend_dependencies,
    "react-markdown dependency is missing.",
)

require(
    frontend_dependencies.get(
        "remark-gfm",
    ) == "4.0.1",
    "remark-gfm must be pinned to 4.0.1.",
)

root_package = json.loads(
    read_text(ROOT_PACKAGE)
)

root_scripts = root_package.get(
    "scripts",
    {},
)

require(
    root_scripts.get(
        "smoke:phase-as-ui",
    )
    == (
        "python "
        "scripts/69_smoke_chat_markdown_rendering.py"
    ),
    "smoke:phase-as-ui alias is invalid.",
)

require(
    root_scripts.get(
        "smoke:phase-as",
    )
    == (
        "npm run smoke:phase-as-ui "
        "&& npm run smoke:phase-ar"
    ),
    "smoke:phase-as alias is invalid.",
)

documentation_requirements = (
    (
        CAPABILITIES,
        "Phase AS implementation contract",
    ),
    (
        LOCAL_AUDIT,
        "Safe Markdown chat rendering after Phase AS",
    ),
    (
        ROADMAP,
        "Phase AS safe Markdown message rendering",
    ),
    (
        STATUS,
        "Checkpoint Phase AS safe Markdown message rendering",
    ),
)

for path, marker in documentation_requirements:
    require(
        marker in read_text(path),
        f"Missing documentation marker in {path}: {marker}",
    )

print("PHASE_AS_MARKDOWN_RENDERING_SMOKE_OK")
