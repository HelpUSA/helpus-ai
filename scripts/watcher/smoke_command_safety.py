import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT  / "backend"))

from command_safety import CommandSafetyPolicy

safe = CommandSafetyPolicy.validate(["git", "status", "-sb"])
assert safe.allowed is True
assert safe.requires_dry_run is False

danger = CommandSafetyPolicy.validate(["powershell", "-Command", "Remove-Item temp -Recurse"])
assert danger.allowed is False
assert danger.requires_dry_run is True

allowed = CommandSafetyPolicy.validate(["powershell", "-Command", "Remove-Item temp -Recurse"], dry_run_confirmed=True)
assert allowed.allowed is True
assert allowed.requires_dry_run is True

bad = CommandSafetyPolicy.validate(["git", ""])
assert bad.allowed is False

print("COMMAND_SAFETY_SMOKE_OK")
