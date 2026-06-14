import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.operational_context import load_operational_context, missing_required_docs, render_operational_summary

missing = missing_required_docs()
if missing:
    raise AssertionError('Missing required docs: ' + repr(missing))

context = load_operational_context()
for key in ['repo', 'branch', 'remote', 'docs_loaded', 'safe_validation_commands', 'safety_rules', 'next_micro']:
    if key not in context:
        raise AssertionError('Missing context key: ' + key)

summary = render_operational_summary()
for marker in ['operational_context_status=ready', 'repo=D:/dev/ai', 'branch=main', 'next=Micro 25 - watcher_intent']:
    if marker not in summary:
        raise AssertionError('Missing summary marker: ' + marker)

commands = context['safe_validation_commands']
for command in ['git status -sb', 'python scripts/watcher/smoke_operational_release.py', 'python scripts/watcher/smoke_health_report.py', 'npm --prefix frontend run build', 'git diff --check']:
    if command not in commands:
        raise AssertionError('Missing validation command: ' + command)

rules = ' '.join(context['safety_rules'])
for marker in ['AI_LOCAL receipts', 'watcher', 'Do not deploy', 'destructive commands']:
    if marker not in rules:
        raise AssertionError('Missing safety marker: ' + marker)

print('OPERATIONAL_CONTEXT_SMOKE_OK')
