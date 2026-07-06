from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / 'frontend' / 'src' / 'app' / 'admin' / 'local' / 'page.tsx'

text = PAGE.read_text(encoding='utf-8')
required_markers = [
    'Operador local read-only',
    '/local/status',
    '/local/diff',
    '/local/files/list?path=docs%2F&limit=25',
    '/local/docs/search?q=HelpUS%20AI&path=docs%2F&limit=10',
    'Authorization: `Bearer ${googleToken}`',
    'Voltar ao admin',
]
missing = [marker for marker in required_markers if marker not in text]
if missing:
    raise SystemExit(f'missing markers: {missing}')
print('OK smoke_admin_local_readonly_panel')
