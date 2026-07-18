import py_compile,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=[
".github/workflows/multi-ai-foundation.yml","docs/ai/HELPUS_MULTI_AI_CLOUD_ARCHITECTURE.md","docs/obsidian/HELPUSAI_STATUS_2026-07-18_MULTI_AI_FOUNDATION.md","infra/multi-ai/.env.example","infra/multi-ai/.gitignore","infra/multi-ai/docker-compose.yml","infra/multi-ai/litellm-config.yaml","services/multi_ai_router/Dockerfile","services/multi_ai_router/__init__.py","services/multi_ai_router/app.py","services/multi_ai_router/requirements.txt","services/multi_ai_router/router_core.py","tests/test_multi_ai_router_core.py","scripts/82_validate_multi_ai_foundation.py"]
ALIASES=["helpus-fast","helpus-general","helpus-reasoner","helpus-code","helpus-vision","helpus-verifier","helpus-embedding"]
def need(value,message):
    if not value: raise RuntimeError(message)
for rel in FILES: need((ROOT/rel).is_file(),"missing "+rel)
config=(ROOT/"infra/multi-ai/litellm-config.yaml").read_text(encoding="utf-8")
for alias in ALIASES: need("model_name: "+alias in config,"missing alias "+alias)
for rel in FILES:
    for number,line in enumerate((ROOT/rel).read_text(encoding="utf-8").splitlines(),1):
        need(line==line.rstrip(" \t"),f"trailing whitespace {rel}:{number}")
for rel in ["services/multi_ai_router/__init__.py","services/multi_ai_router/app.py","services/multi_ai_router/router_core.py","tests/test_multi_ai_router_core.py","scripts/82_validate_multi_ai_foundation.py"]:
    py_compile.compile(str(ROOT/rel),doraise=True)
p=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests"),"-p","test_multi_ai_router_core.py","-v"],cwd=ROOT,text=True,capture_output=True)
print(p.stdout,end=""); print(p.stderr,end="",file=sys.stderr)
need(p.returncode==0,"unit tests failed")
print("MULTI_AI_FOUNDATION_VALID=True")
print("MODEL_ALIAS_COUNT=7")
print("UNIT_TESTS_OK=True")
