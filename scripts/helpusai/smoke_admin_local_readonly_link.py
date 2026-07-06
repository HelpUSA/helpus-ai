from pathlib import Path

admin_page = Path('frontend/src/app/admin/page.tsx')
text = admin_page.read_text(encoding='utf-8')
required = [
    'href="/admin/local"',
    'Operador local read-only',
]
missing = [marker for marker in required if marker not in text]
if missing:
    raise SystemExit(f'missing admin local link markers: {missing}')
print('OK smoke_admin_local_readonly_link')
