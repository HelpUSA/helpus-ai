from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WatcherIntent:
    category: str
    should_build_envelope: bool
    should_stop: bool
    reason: str


def classify_watcher_intent(text: str) -> dict:
    value = (text or "").lower()

    if "[ai_local_erro]" in value or "envelope_parse_error" in value:
        return asdict(WatcherIntent("recover", True, False, "parse error receipt; create new command_id"))

    if "[ai_local_run]" in value and ("status=failed" in value or "return_code=1" in value):
        return asdict(WatcherIntent("recover", True, False, "failed receipt; inspect before fixing"))

    if "[ai_local_run]" in value or "status=acked" in value or "return_code=0" in value:
        return asdict(WatcherIntent("result", False, False, "successful receipt; summarize result"))

    if any(term in value for term in ["deploy", "reset --hard", "git clean", "secret", "production"]):
        return asdict(WatcherIntent("stop", False, True, "sensitive action requires authorization"))

    if any(term in value for term in ["corrija", "reenvie", "falhou", "erro", "recupera"]):
        return asdict(WatcherIntent("recover", True, False, "recovery requested"))

    if any(term in value for term in ["status", "inspecione", "verifique", "veja", "analise", "proximas"]):
        return asdict(WatcherIntent("inspect", True, False, "inspection requested"))

    if any(term in value for term in ["valide", "validar", "smoke", "build"]):
        return asdict(WatcherIntent("validate", True, False, "validation requested"))

    if any(term in value for term in ["commit", "commitar"]):
        return asdict(WatcherIntent("commit", True, False, "commit requested"))

    if any(term in value for term in ["tag", "baseline"]):
        return asdict(WatcherIntent("tag", True, False, "tag requested"))

    if any(term in value for term in ["prossiga", "continue", "pode fazer", "pode ir", "siga"]):
        return asdict(WatcherIntent("patch", True, False, "continue requested"))

    return asdict(WatcherIntent("inspect", True, False, "default safe inspection"))
