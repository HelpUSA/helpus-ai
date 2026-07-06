from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.local_safe_plan import plan_local_action


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


phase_a = plan_local_action({"intent": "phase_a_validation"})
assert_true(phase_a["ok"] is True, phase_a)
assert_true(phase_a["mode"] == "plan_only", phase_a)
assert_true(phase_a["executed"] is False, phase_a)
assert_true(phase_a["allowed"] is True, phase_a)
assert_true(phase_a["risk"] == "readonly", phase_a)
assert_true(phase_a["commands"] == ["npm run smoke:phase-a"], phase_a)
assert_true(phase_a["requires_human_confirmation"] is True, phase_a)

status = plan_local_action({"intent": "local_status"})
assert_true(status["allowed"] is True, status)
assert_true(status["commands"] == ["git status -sb"], status)

custom_readonly = plan_local_action({"command": "git diff --check"})
assert_true(custom_readonly["allowed"] is True, custom_readonly)
assert_true(custom_readonly["executed"] is False, custom_readonly)

blocked = plan_local_action({"command": "git push origin main"})
assert_true(blocked["allowed"] is False, blocked)
assert_true(blocked["risk"] == "blocked", blocked)
assert_true(any("git push" in reason for reason in blocked["blocked_reasons"]), blocked)
assert_true(blocked["executed"] is False, blocked)

unknown = plan_local_action({"intent": "custom", "command": "python scripts/custom_task.py"})
assert_true(unknown["allowed"] is False, unknown)
assert_true(unknown["risk"] == "needs_review", unknown)
assert_true(unknown["executed"] is False, unknown)

empty = plan_local_action({"intent": "custom"})
assert_true(empty["ok"] is False, empty)
assert_true(empty["reason"] == "no_command_or_known_intent", empty)

main_text = (ROOT / 'backend' / 'main.py').read_text(encoding='utf-8')
assert_true('@app.post("/local/plan")' in main_text, 'missing /local/plan endpoint')
assert_true('plan_local_action(request)' in main_text, 'missing plan_local_action call')

print('SMOKE_LOCAL_SAFE_PLAN_OK')
