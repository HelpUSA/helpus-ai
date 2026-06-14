from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.watcher_recovery import analyze_watcher_failure, render_recovery_summary


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f'{message}: expected {expected!r}, got {actual!r}')


def assert_contains(text, marker, message):
    if marker not in text:
        raise AssertionError(f'{message}: expected {marker!r} in {text!r}')


def main() -> None:
    parse_error = analyze_watcher_failure('[AI_LOCAL_ERRO] tipo=envelope_parse_error')
    assert_equal(parse_error['category'], 'envelope_parse_error', 'parse category')
    assert_equal(parse_error['executed'], False, 'parse executed')
    assert_equal(parse_error['next_action'], 'create_new_command_id_and_simpler_envelope', 'parse next action')

    success = analyze_watcher_failure('[AI_LOCAL_RUN] status=acked return_code=0')
    assert_equal(success['category'], 'success', 'success category')
    assert_equal(success['executed'], True, 'success executed')

    failed = analyze_watcher_failure('[AI_LOCAL_RUN] status=failed return_code=1')
    assert_equal(failed['category'], 'command_failed', 'failed category')
    assert_equal(failed['risk'], 'partial_change_possible', 'failed risk')

    diff_check = analyze_watcher_failure('RUN git diff --check failed')
    assert_equal(diff_check['category'], 'diff_check_failed', 'diff check category')
    assert_equal(diff_check['next_action'], 'fix_diff_check_only_then_revalidate', 'diff check next action')

    build = analyze_watcher_failure('FRONTEND_BUILD npm --prefix frontend run build Next build failed')
    assert_equal(build['category'], 'build_failed', 'build category')
    assert_equal(build['next_action'], 'inspect_build_error_before_patch', 'build action')

    smoke = analyze_watcher_failure('RUN python scripts/watcher/smoke_x.py Traceback AssertionError')
    assert_equal(smoke['category'], 'smoke_failed', 'smoke category')
    assert_equal(smoke['next_action'], 'inspect_failed_smoke_before_patch', 'smoke action')

    syntax = analyze_watcher_failure('SyntaxError unexpected indent')
    assert_equal(syntax['category'], 'syntax_or_indent_failed', 'syntax category')
    assert_equal(syntax['next_action'], 'patch_only_broken_file_then_py_compile', 'syntax action')

    unknown = analyze_watcher_failure('aguarde')
    assert_equal(unknown['category'], 'unknown', 'unknown category')
    assert_equal(unknown['executed'], False, 'unknown executed')

    summary = render_recovery_summary('[AI_LOCAL_ERRO] envelope_parse_error')
    assert_contains(summary, 'category=envelope_parse_error', 'summary category')
    assert_contains(summary, 'executed=False', 'summary executed')

    print('WATCHER_RECOVERY_SMOKE_OK')


if __name__ == '__main__':
    main()
