
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend/main.py"

assert TARGET.exists(), f"missing target: {TARGET}"

source = TARGET.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

tree = ast.parse(
    source,
    filename=str(TARGET),
)

chat_functions = [
    node
    for node in ast.walk(tree)
    if (
        isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name == "chat"
    )
]

assert len(chat_functions) == 1, (
    f"expected one chat function, "
    f"found {len(chat_functions)}"
)

chat = chat_functions[0]

arguments = {
    arg.arg
    for arg in (
        list(chat.args.posonlyargs)
        + list(chat.args.args)
        + list(chat.args.kwonlyargs)
    )
}

assert "request" in arguments, (
    "chat request argument is missing"
)

assignments = []

for node in ast.walk(chat):
    if isinstance(node, ast.Assign):
        if any(
            isinstance(target, ast.Name)
            and target.id
            == "_helpus_user_message_for_lessons"
            for target in node.targets
        ):
            assignments.append(node)

    elif isinstance(node, ast.AnnAssign):
        if (
            isinstance(node.target, ast.Name)
            and node.target.id
            == "_helpus_user_message_for_lessons"
        ):
            assignments.append(node)

assert len(assignments) == 1, (
    "expected exactly one lesson-message assignment"
)

value = assignments[0].value

loaded_names = [
    child.id
    for child in ast.walk(value)
    if (
        isinstance(child, ast.Name)
        and isinstance(child.ctx, ast.Load)
    )
]

assert "mensagem" not in loaded_names, (
    "undefined mensagem reference returned"
)

assert loaded_names.count("request") == 3, (
    "lesson-message extraction must use request "
    "exactly three times"
)

assert not any(
    isinstance(node, ast.Attribute)
    and node.attr
    == "_helpus_user_message_for_lessons"
    for node in ast.walk(chat)
), "corrupted self-referential attribute found"

for marker in [
    'getattr(request, "mensagem", None)',
    'getattr(request, "message", None)',
    'getattr(request, "pergunta", None)',
    "user_message=str(_helpus_user_message_for_lessons)",
]:
    assert marker in source, (
        f"missing corrected binding marker: {marker}"
    )

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in source, (
        f"forbidden execution marker found: {forbidden}"
    )

print("SMOKE_CHAT_MESSAGE_BINDING_PRECISE_OK")
