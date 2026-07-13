
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'backend/main.py'
FUNCTION = 'chat'
REPLACEMENT = '_helpus_user_message_for_lessons'

assert TARGET.exists(), f"missing target file: {TARGET}"

text = TARGET.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

tree = ast.parse(
    text,
    filename=str(TARGET),
)

matched = []

for node in ast.walk(tree):
    if not isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        continue

    if node.name != FUNCTION:
        continue

    loaded = [
        child
        for child in ast.walk(node)
        if (
            isinstance(child, ast.Name)
            and isinstance(child.ctx, ast.Load)
        )
    ]

    assert not any(
        child.id == "mensagem"
        for child in loaded
    ), "undefined mensagem reference returned"

    assert any(
        child.id == REPLACEMENT
        for child in loaded
    ), "replacement variable is not used"

    matched.append(node)

assert len(matched) == 1, (
    f"expected one function {FUNCTION!r}, "
    f"found {len(matched)}"
)

print("SMOKE_CHAT_MESSAGE_NAMEERROR_OK")
