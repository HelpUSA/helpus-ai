from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.local_safe_plan import list_local_plan_intents, plan_local_action
def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)
intents = list_local_plan_intents()
assert_true(intents["ok"] is True, intents)
assert_true(intents["mode"] == "plan_only", intents)
assert_true(intents["executed"] is False, intents)
intent_names = {item["intent"] for item in intents["intents"]}
assert_true("phase_b_validation" in intent_names, intents)
assert_true("local_recent_commits" in intent_names, intents)
phase_b = plan_local_action({"intent": "phase_b_validation"})
assert_true(phase_b["allowed"] is True, phase_b)
assert_true(phase_b["commands"] == ["npm run smoke:phase-b"], phase_b)
assert_true(phase_b["version"] == "local-plan-v1", phase_b)
assert_true(phase_b["executed"] is False, phase_b)
chain = plan_local_action({"command": "git diff --check && git push origin main"})
assert_true(chain["allowed"] is False, chain)
assert_true(chain["risk"] == "blocked", chain)
assert_true(any(reason.startswith("blocked_separator:") for reason in chain["blocked_reasons"]), chain)
assert_true(any("git push" in reason for reason in chain["blocked_reasons"]), chain)
long_command = "git status " + ("x" * 260)
long_plan = plan_local_action({"command": long_command})
assert_true(long_plan["allowed"] is False, long_plan)
assert_true(any(reason.startswith("command_too_long") for reason in long_plan["blocked_reasons"]), long_plan)
many = plan_local_action({"commands": ["git status -sb"] * 6})
assert_true(many["allowed"] is False, many)
assert_true(many["reason"] == "too_many_commands", many)
main_text = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
assert_true('@app.get("/local/plan/intents")' in main_text, "missing /local/plan/intents endpoint")
print("SMOKE_LOCAL_PLAN_CONTRACT_OK")
