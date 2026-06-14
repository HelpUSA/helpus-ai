from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WatcherRecovery:
    category: str
    executed: bool
    risk: str
    next_action: str
    reason: str


def _result(category: str, executed: bool, risk: str, next_action: str, reason: str) -> dict:
    return asdict(WatcherRecovery(category, executed, risk, next_action, reason))


def analyze_watcher_failure(text: str) -> dict:
    value = (text or '').lower()

    if 'envelope_parse_error' in value or '[ai_local_erro]' in value:
        return _result('envelope_parse_error', False, 'none_executed', 'create_new_command_id_and_simpler_envelope', 'parse error receipt means nothing was executed')

    if 'return_code=0' in value or ('status=acked' in value and 'return_code=1' not in value):
        return _result('success', True, 'none', 'summarize_result_and_continue', 'watcher reported a successful run')

    if 'git diff --check' in value or 'diff_check' in value:
        return _result('diff_check_failed', True, 'format_or_whitespace', 'fix_diff_check_only_then_revalidate', 'diff check failed and should be corrected narrowly')

    if 'next build' in value or 'npm --prefix frontend run build' in value or 'frontend_build' in value:
        return _result('build_failed', True, 'build_or_type_error', 'inspect_build_error_before_patch', 'frontend build failed')

    if 'smoke' in value and ('traceback' in value or 'assertionerror' in value or 'return_code=1' in value):
        return _result('smoke_failed', True, 'contract_regression_possible', 'inspect_failed_smoke_before_patch', 'a smoke test failed')

    if 'syntaxerror' in value or 'indentationerror' in value:
        return _result('syntax_or_indent_failed', True, 'python_file_broken', 'patch_only_broken_file_then_py_compile', 'python syntax or indentation failed')

    if 'return_code=1' in value or 'status=failed' in value or 'traceback' in value:
        return _result('command_failed', True, 'partial_change_possible', 'inspect_status_and_diff_before_fix', 'command executed but failed')

    return _result('unknown', False, 'unknown', 'inspect_status_and_logs_before_action', 'failure type was not recognized')


def render_recovery_summary(text: str) -> str:
    recovery = analyze_watcher_failure(text)
    return 'category={category} executed={executed} risk={risk} next_action={next_action}'.format(**recovery)
