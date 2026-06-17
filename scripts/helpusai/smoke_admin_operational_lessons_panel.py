import importlib
import pathlib
import sys

root = pathlib.Path.cwd()
sys.path.insert(0, str(root / 'backend'))

module = importlib.import_module('helpus_operational_lessons')
panel = module.build_admin_operational_lessons_panel()

assert panel['readonly'] is True
assert panel['statuses'] == ['candidate', 'promoted', 'rejected']
for status in panel['statuses']:
 assert status in panel['counts']
 assert status in panel['lessons']
assert panel['counts']['candidate'] >= 1

main_text = (root / 'backend' / 'main.py').read_text(encoding='utf-8')
assert '/admin/operational-lessons' in main_text
assert 'Depends(obter_admin_google)' in main_text
assert 'build_admin_operational_lessons_panel' in main_text

print('OK smoke_admin_operational_lessons_panel')
