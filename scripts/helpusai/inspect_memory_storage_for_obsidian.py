from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "HELPUSAI_MEMORY_STORAGE_OBSIDIAN_EXPORT_INSPECTION_2026-06-17.md"

CANDIDATE_PATHS = [
    "backend/helpus_internal_memory_recorder.py",
    "backend/helpus_memory_reader.py",
    "backend/helpus_memory_context.py",
    "backend/helpus_operational_lessons.py",
    "backend/helpus_operational_lesson_context.py",
    "backend/main.py",
]

SEARCH_DIRS = [
    "backend",
    "migrations",
    "docs",
    "scripts/helpusai",
]


@dataclass(frozen=True)
class FileFinding:
    path: str
    exists: bool
    lines: int = 0
    functions: tuple[str, ...] = ()
    classes: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()
    sql_tables: tuple[str, ...] = ()
    env_vars: tuple[str, ...] = ()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_python_symbols(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return (), ()

    functions: list[str] = []
    classes: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return tuple(sorted(set(functions))), tuple(sorted(set(classes)))


def find_markers(text: str) -> tuple[str, ...]:
    candidates = [
        "safe_record_chat_memory_event",
        "record_operational_lesson_candidate",
        "record_ai_local_error_lesson",
        "operational_lesson",
        "kind",
        "extra",
        "project_id",
        "conversation_id",
        "provider",
        "route",
        "user_message",
        "assistant_reply",
        "DATABASE_URL",
        "POSTGRES",
        "memory",
        "memorias",
        "chat_memory",
        "helpus_memory",
    ]

    found: list[str] = []
    lowered = text.lower()

    for candidate in candidates:
        if candidate.lower() in lowered:
            found.append(candidate)

    return tuple(found)


def find_sql_tables(text: str) -> tuple[str, ...]:
    patterns = [
        r"create\s+table\s+(?:if\s+not\s+exists\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
        r"insert\s+into\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"from\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"update\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    ]

    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            table = match.group(1)
            if table.lower() not in {"select", "where", "returning"} and table not in found:
                found.append(table)

    return tuple(found)


def find_env_vars(text: str) -> tuple[str, ...]:
    found = sorted(set(re.findall(r"[A-Z][A-Z0-9_]{4,}", text)))
    interesting = [
        item
        for item in found
        if any(key in item for key in ("DATABASE", "POSTGRES", "MEMORY", "HELPUS", "DB", "SUPABASE"))
    ]
    return tuple(interesting)


def inspect_file(path_text: str) -> FileFinding:
    path = ROOT / path_text
    if not path.exists():
        return FileFinding(path=path_text, exists=False)

    text = read_text(path)
    functions, classes = parse_python_symbols(text) if path.suffix == ".py" else ((), ())

    return FileFinding(
        path=path_text,
        exists=True,
        lines=len(text.splitlines()),
        functions=functions,
        classes=classes,
        markers=find_markers(text),
        sql_tables=find_sql_tables(text),
        env_vars=find_env_vars(text),
    )


def collect_repository_search() -> dict[str, list[str]]:
    patterns = {
        "operational_lesson": [],
        "safe_record_chat_memory_event": [],
        "DATABASE_URL": [],
        "insert into": [],
        "create table": [],
        "jsonb": [],
        "extra": [],
    }

    files: list[Path] = []
    for dirname in SEARCH_DIRS:
        root = ROOT / dirname
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".sql", ".txt"})

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        text = read_text(path)
        lowered = text.lower()

        for pattern in patterns:
            if pattern.lower() in lowered:
                patterns[pattern].append(rel)

    return {key: sorted(set(value)) for key, value in patterns.items()}


def infer_next_steps(findings: list[FileFinding], repo_search: dict[str, list[str]]) -> list[str]:
    tables = sorted({table for finding in findings for table in finding.sql_tables})
    env_vars = sorted({env for finding in findings for env in finding.env_vars})

    steps: list[str] = []

    if "safe_record_chat_memory_event" in {
        marker for finding in findings for marker in finding.markers
    }:
        steps.append("Recorder de memoria existe e deve ser usado como fonte primaria para entender payloads gravados.")

    if any("operational_lesson" in marker for finding in findings for marker in finding.markers):
        steps.append("Operational lessons ja possuem payload estruturado; exportador real deve filtrar registros com kind=operational_lesson.")

    if tables:
        steps.append("Ha tabelas SQL detectadas; proximo patch deve mapear tabela/colunas reais antes de consultar producao.")
    else:
        steps.append("Nenhuma tabela SQL conclusiva foi detectada apenas por regex; proximo patch deve inspecionar recorder e migrations com mais detalhe.")

    if env_vars:
        steps.append("Variaveis de ambiente relacionadas a DB/memoria foram detectadas; exportador real deve ser opt-in e readonly.")
    else:
        steps.append("Nenhuma variavel de banco foi confirmada no codigo inspecionado; manter exportador real com fallback para lessons embutidas.")

    if repo_search.get("jsonb"):
        steps.append("Ha indicio de JSON/JSONB; exportador deve procurar campos extra/payload para kind=operational_lesson.")

    return steps


def render_report(findings: list[FileFinding], repo_search: dict[str, list[str]]) -> str:
    lines: list[str] = [
        "# HelpUSAI Memory Storage Inspection for Obsidian Export",
        "",
        "Data: 2026-06-17",
        "",
        "## Objetivo",
        "",
        "Inspecionar a implementacao local de memoria da HelpUSAI antes de criar exportacao de lessons reais do banco para o vault Obsidian.",
        "",
        "## Resultado resumido",
        "",
        "- Inspecao readonly.",
        "- Nenhuma conexao externa foi aberta.",
        "- Nenhuma migracao foi executada.",
        "- Nenhum dado de producao foi lido.",
        "- O objetivo e descobrir pontos de integracao seguros para o proximo patch.",
        "",
        "## Arquivos inspecionados",
        "",
    ]

    for finding in findings:
        lines.append(f"### {finding.path}")
        lines.append("")
        lines.append(f"- exists: `{finding.exists}`")
        if finding.exists:
            lines.append(f"- lines: `{finding.lines}`")
            lines.append(f"- classes: `{', '.join(finding.classes) if finding.classes else 'none'}`")
            lines.append(f"- functions: `{', '.join(finding.functions) if finding.functions else 'none'}`")
            lines.append(f"- markers: `{', '.join(finding.markers) if finding.markers else 'none'}`")
            lines.append(f"- sql_tables_detected: `{', '.join(finding.sql_tables) if finding.sql_tables else 'none'}`")
            lines.append(f"- env_vars_detected: `{', '.join(finding.env_vars) if finding.env_vars else 'none'}`")
        lines.append("")

    lines.extend(
        [
            "## Busca agregada no repositório",
            "",
        ]
    )

    for pattern, paths in repo_search.items():
        lines.append(f"### `{pattern}`")
        lines.append("")
        if paths:
            for path in paths[:30]:
                lines.append(f"- {path}")
            if len(paths) > 30:
                lines.append(f"- ... mais {len(paths) - 30} arquivo(s)")
        else:
            lines.append("- nenhum arquivo encontrado")
        lines.append("")

    lines.extend(
        [
            "## Inferência operacional",
            "",
        ]
    )

    for step in infer_next_steps(findings, repo_search):
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Recomendação para o bloco 15B",
            "",
            "Criar exportador real em modo readonly e opt-in com a seguinte ordem:",
            "",
            "1. Reusar o formato de payload de `helpus_operational_lessons.py`.",
            "2. Detectar registros com `kind=operational_lesson` quando o storage real estiver acessivel.",
            "3. Exportar para `knowledge/obsidian/HelpUSAI/Operational Lessons/Runtime/`.",
            "4. Manter fallback para lessons embutidas caso o banco nao esteja acessivel.",
            "5. Criar smoke sem depender de banco externo.",
            "",
            "## Marcadores obrigatórios para smoke",
            "",
            "- MEMORY_STORAGE_OBSIDIAN_INSPECTION_OK",
            "- operational_lesson",
            "- safe_record_chat_memory_event",
            "- Obsidian",
            "- readonly",
            "",
            "MEMORY_STORAGE_OBSIDIAN_INSPECTION_OK",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    findings = [inspect_file(path) for path in CANDIDATE_PATHS]
    repo_search = collect_repository_search()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(findings, repo_search), encoding="utf-8")

    print("MEMORY_STORAGE_OBSIDIAN_INSPECTION_WRITTEN")
    print(REPORT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
