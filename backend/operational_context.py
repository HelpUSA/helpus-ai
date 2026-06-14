from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    'docs/HELPUS_PROJECT_MASTER.md',
]

OPTIONAL_DOCS = [
    'docs/legacy/HELPUS_AGENT_OPERATING_PROTOCOL.md',
    'docs/legacy/HELPUS_WATCHER_COMMAND_PROTOCOL.md',
    'docs/legacy/HELPUS_CHAT_WATCHER_INTELLIGENCE_ROADMAP.md',
    'docs/legacy/HELPUS_OPERATIONAL_AUTOMATION.md',
    'docs/legacy/HELPUS_LOCAL_AI_PROVIDER.md',
]


def missing_required_docs(root=None):
    base = Path(root) if root else ROOT
    return [path for path in REQUIRED_DOCS if not (base / path).exists()]


def title_from_text(text, fallback):
    for line in text.splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return fallback


def load_operational_context(root=None):
    base = Path(root) if root else ROOT
    docs = []
    for rel in REQUIRED_DOCS + OPTIONAL_DOCS:
        path = base / rel
        if path.exists():
            text = path.read_text(encoding='utf-8-sig', errors='replace')
            docs.append({'path': rel, 'title': title_from_text(text, rel), 'length': len(text)})
    return {
        'repo': 'D:/dev/ai',
        'branch': 'main',
        'remote': 'origin/main',
        'missing_required_docs': missing_required_docs(base),
        'docs_loaded': docs,
        'safe_validation_commands': [
            'git status -sb',
            'python scripts/watcher/smoke_watcher_recovery.py',
            'python scripts/watcher/smoke_operational_release.py',
            'python scripts/watcher/smoke_health_report.py',
            'npm --prefix frontend run build',
            'git diff --check',
        ],
        'safety_rules': [
            'Do not treat AI_LOCAL receipts as new commands.',
            'Use watcher for execution; local AI is analysis only.',
            'Use CommandBuilder plus PreflightValidator before proposing watcher envelopes.',
            'In parse errors, create a new command_id and simplify the envelope.',
            'In partial failures, inspect status and diff before fixing.',
            'Do not deploy without explicit authorization.',
            'Do not run destructive commands without dry-run and explicit authorization.',
        ],
        'next_micro': 'Micro 28 - chat_watcher_orchestrator',
    }


def render_operational_summary(root=None):
    context = load_operational_context(root)
    status = 'ready' if not context['missing_required_docs'] else 'missing_required_docs'
    lines = [
        'operational_context_status=' + status,
        'repo=' + context['repo'],
        'branch=' + context['branch'],
        'docs_loaded=' + str(len(context['docs_loaded'])),
        'missing_required_docs=' + str(len(context['missing_required_docs'])),
        'next=' + context['next_micro'],
    ]
    if context['missing_required_docs']:
        lines.append('missing=' + ','.join(context['missing_required_docs']))
    return chr(10).join(lines)
