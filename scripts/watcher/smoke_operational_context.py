from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.operational_context import load_operational_context, render_operational_summary


context = load_operational_context(ROOT)
missing = context['missing_required_docs']
if missing:
    raise AssertionError('Missing required docs: ' + repr(missing))

loaded_paths = [doc['path'] for doc in context['docs_loaded']]
if 'docs/HELPUS_PROJECT_MASTER.md' not in loaded_paths:
    raise AssertionError('Master doc not loaded')

if context['repo'] != 'D:/dev/ai':
    raise AssertionError('Unexpected repo: ' + context['repo'])

if context['branch'] != 'main':
    raise AssertionError('Unexpected branch: ' + context['branch'])

if 'Final - docs_and_report' != context['next_micro']:
    raise AssertionError('Unexpected next_micro: ' + context['next_micro'])

rules = ' '.join(context['safety_rules'])
for marker in ['AI_LOCAL receipts', 'new command_id', 'Do not deploy']:
    if marker not in rules:
        raise AssertionError('Missing safety rule marker: ' + marker)

summary = render_operational_summary(ROOT)
for marker in [
    'operational_context_status=ready',
    'repo=D:/dev/ai',
    'docs_loaded=',
    'missing_required_docs=0',
    'next=Final - docs_and_report',
]:
    if marker not in summary:
        raise AssertionError('Missing summary marker: ' + marker)

print('OPERATIONAL_CONTEXT_SMOKE_OK')
