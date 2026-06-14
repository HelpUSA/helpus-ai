import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.watcher_intent import classify_watcher_intent

cases = [
    ("prossiga", "patch", True, False),
    ("quais as proximas atividades?", "inspect", True, False),
    ("valide a suite", "validate", True, False),
    ("faca commit", "commit", True, False),
    ("crie tag", "tag", True, False),
    ("corrija e reenvie", "recover", True, False),
    ("[AI_LOCAL_ERRO] tipo=envelope_parse_error", "recover", True, False),
    ("[AI_LOCAL_RUN] status=failed return_code=1", "recover", True, False),
    ("[AI_LOCAL_RUN] status=acked return_code=0", "result", False, False),
    ("deploy agora", "stop", False, True),
    ("git reset --hard", "stop", False, True),
]

for text, category, should_build, should_stop in cases:
    result = classify_watcher_intent(text)
    if result["category"] != category:
        raise AssertionError((text, result, category))
    if result["should_build_envelope"] != should_build:
        raise AssertionError((text, result, should_build))
    if result["should_stop"] != should_stop:
        raise AssertionError((text, result, should_stop))

print("WATCHER_INTENT_SMOKE_OK")
