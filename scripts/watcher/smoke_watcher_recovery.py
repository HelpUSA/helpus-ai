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


    ai_local_run_failed = analyze_watcher_failure('[AI_LOCAL_RUN] id=x status=failed return_code=1 smoke stderr=Traceback')
    assert_equal(ai_local_run_failed['category'], 'smoke_failed', 'ai local run failed category')
    assert_equal(ai_local_run_failed['executed'], True, 'ai local run failed executed')
    assert_equal(ai_local_run_failed['next_action'], 'inspect_failed_smoke_before_patch', 'ai local run failed action')

    ai_local_run_success = analyze_watcher_failure('[AI_LOCAL_RUN] id=x status=acked return_code=0 stdout=OK')
    assert_equal(ai_local_run_success['category'], 'success', 'ai local run success category')
    assert_equal(ai_local_run_success['executed'], True, 'ai local run success executed')
    assert_equal(ai_local_run_success['next_action'], 'summarize_result_and_continue', 'ai local run success action')

    ai_local_erro_parse = analyze_watcher_failure('[AI_LOCAL_ERRO] tipo=envelope_parse_error executado=nao')
    assert_equal(ai_local_erro_parse['category'], 'envelope_parse_error', 'ai local erro category')
    assert_equal(ai_local_erro_parse['executed'], False, 'ai local erro executed')
    assert_equal(ai_local_erro_parse['risk'], 'none_executed', 'ai local erro risk')

    diff_check_receipt = analyze_watcher_failure('[AI_LOCAL_RUN] return_code=1 stdout=DIFF_CHECK git diff --check')
    assert_equal(diff_check_receipt['category'], 'diff_check_failed', 'receipt diff check category')
    assert_equal(diff_check_receipt['risk'], 'format_or_whitespace', 'receipt diff check risk')



    generic_failed = analyze_watcher_failure('[AI_LOCAL_RUN] id=x status=failed return_code=1 stderr=generic failure')
    assert_equal(generic_failed['category'], 'command_failed', 'generic command failed category')
    assert_equal(generic_failed['executed'], True, 'generic command failed executed')
    assert_equal(generic_failed['next_action'], 'inspect_status_and_diff_before_fix', 'generic command failed action')

    build_failed = analyze_watcher_failure('[AI_LOCAL_RUN] id=x status=failed return_code=1 stdout=FRONTEND_BUILD frontend_build npm --prefix frontend run build')
    assert_equal(build_failed['category'], 'build_failed', 'frontend build failed category')
    assert_equal(build_failed['risk'], 'build_or_type_error', 'frontend build failed risk')

    syntax_failed = analyze_watcher_failure('[AI_LOCAL_RUN] id=x status=failed return_code=1 stderr=SyntaxError invalid syntax')
    assert_equal(syntax_failed['category'], 'syntax_or_indent_failed', 'syntax failed category')
    assert_equal(syntax_failed['next_action'], 'patch_only_broken_file_then_py_compile', 'syntax failed action')

    unknown_receipt = analyze_watcher_failure('unrecognized watcher text without status markers')
    assert_equal(unknown_receipt['category'], 'unknown', 'unknown receipt category')
    assert_equal(unknown_receipt['executed'], False, 'unknown receipt executed')

    print('WATCHER_RECOVERY_SMOKE_OK')


if __name__ == '__main__':
    main()
