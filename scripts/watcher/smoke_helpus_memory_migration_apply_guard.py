import os
import subprocess
import sys

cmd = [sys.executable, "scripts/railway/apply_helpus_memory_migration.py"]

env = os.environ.copy()
env.pop("HELPUS_APPLY_MEMORY_MIGRATION", None)

result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

if result.returncode != 3:
    print(result.stdout)
    print(result.stderr)
    raise SystemExit(f"Expected guarded return code 3, got {result.returncode}")

if "APPLY_BLOCKED" not in result.stdout:
    print(result.stdout)
    raise SystemExit("Guarded apply did not print APPLY_BLOCKED")

if "No SQL was executed." not in result.stdout:
    print(result.stdout)
    raise SystemExit("Guarded apply did not confirm no SQL execution")

print("OK smoke_helpus_memory_migration_apply_guard")
