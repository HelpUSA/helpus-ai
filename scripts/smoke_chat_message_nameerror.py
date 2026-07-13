
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend/main.py"

REQUIRED_ATTRIBUTES = {
    "mensagem",
    "message",
    "pergunta",
}

source = TARGET.read_text(
    encoding="utf-8-sig",
    errors="strict",
)

tree = ast.parse(
    source,
    filename=str(TARGET),
)

chat_functions = [
    node
    for node in ast.walk(tree)
    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    )
    and node.name == "chat"
]

assert len(chat_functions) == 1, (
    "expected exactly one chat function; "
    f"found {len(chat_functions)}"
)

chat = chat_functions[0]
assignments = []

for node in ast.walk(chat):
    if not isinstance(
        node,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    ):
        continue

    targets = (
        node.targets
        if isinstance(node, ast.Assign)
        else [node.target]
    )

    if any(
        isinstance(target, ast.Name)
        and target.id
        == "_helpus_user_message_for_lessons"
        for target in targets
    ):
        assignments.append(node)

assert len(assignments) == 1, (
    "expected exactly one lesson-context assignment; "
    f"found {len(assignments)}"
)

value = assignments[0].value
fallbacks = []

for node in ast.walk(value):
    if not isinstance(node, ast.Call):
        continue

    if not (
        isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
    ):
        continue

    assert len(node.args) >= 2

    attribute_node = node.args[1]

    if not isinstance(
        attribute_node,
        ast.Constant,
    ):
        continue

    attribute = attribute_node.value

    if attribute not in REQUIRED_ATTRIBUTES:
        continue

    source_node = node.args[0]

    assert isinstance(
        source_node,
        ast.Name,
    ), "fallback source is not a simple name"

    fallbacks.append(
        (
            attribute,
            source_node.id,
        )
    )

assert len(fallbacks) == 3, (
    "expected three message fallbacks; "
    f"found {len(fallbacks)}"
)

assert {
    attribute
    for attribute, _ in fallbacks
} == REQUIRED_ATTRIBUTES

assert all(
    source_name == "request"
    for _, source_name in fallbacks
), (
    "all message fallbacks must read "
    "from request"
)

loaded_names = {
    node.id
    for node in ast.walk(value)
    if isinstance(node, ast.Name)
    and isinstance(node.ctx, ast.Load)
}

assert "request" in loaded_names

assert (
    "_helpus_user_message_for_lessons"
    not in loaded_names
), "lesson-context assignment is self-referential"

assert "mensagem" not in loaded_names, (
    "undefined standalone mensagem reference found"
)

print("SMOKE_CHAT_MESSAGE_NAMEERROR_OK")
print("lesson_context_source=request")
print("request_fallback_count=3")
print("self_reference=False")
