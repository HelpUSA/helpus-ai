from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / 'frontend' / 'src' / 'app' / 'admin' / 'local' / 'page.tsx'
text = PAGE.read_text(encoding='utf-8')
required_markers = [
    'POST /local/plan',
    'read-only + plan-only',
    'Planejamento seguro',
    "postLocal<LocalPlanResult>('/local/plan', { intent: 'phase_a_validation' })",
    "postLocal<LocalPlanResult>('/local/plan', { command: 'git push origin main' })",
    'Nenhum comando é executado por este painel.',
    'Exemplo bloqueado: git push origin main',
]
missing = [marker for marker in required_markers if marker not in text]
if missing:
    raise SystemExit(f'missing markers: {missing}')
print('OK smoke_admin_local_safe_plan_panel')
