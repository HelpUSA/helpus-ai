import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import helpus_operational_lesson_context as ctx


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    old_env = dict(os.environ)

    try:
        os.environ.pop(ctx.OPERATIONAL_LESSON_CONTEXT_ENABLED_ENV, None)
        os.environ.pop(ctx.OPERATIONAL_LESSONS_ENABLED_ENV, None)

        check(ctx.operational_lesson_context_enabled() is False, "context should be disabled by default")

        os.environ[ctx.OPERATIONAL_LESSONS_ENABLED_ENV] = "1"
        check(ctx.operational_lesson_context_enabled() is True, "context should inherit lessons enabled flag")

        topics = ctx.detect_operational_lesson_topics(
            user_message="Como enviar send-chat-message com target_chat_id pelo watcher?",
        )
        check("ai_bridge_local_interchat" in topics, "interchat topic not detected")
        check("ai_bridge_local" in topics, "base watcher topic not detected")

        envelope_topics = ctx.detect_operational_lesson_topics(
            user_message="[AI_LOCAL_ERRO] tipo=envelope_parse_error erro=JSON invalido",
        )
        check("ai_bridge_local_envelope" in envelope_topics, "envelope topic not detected")

        delivery_topics = ctx.detect_operational_lesson_topics(
            user_message="submit_not_confirmed_composer_still_has_text",
        )
        check("ai_bridge_local_delivery" in delivery_topics, "delivery topic not detected")

        run_topics = ctx.detect_operational_lesson_topics(
            user_message="run-command local_capability gateway-brain-supervisor",
        )
        check("ai_bridge_local_run_command" in run_topics, "run command topic not detected")

        selected = ctx.select_operational_lessons_for_topics(("ai_bridge_local_interchat",))
        check(selected, "expected selected interchat lessons")
        check(any("send-chat-message" in lesson.correction for lesson in selected), "missing send-chat-message correction")

        context = ctx.build_operational_lesson_context_for_chat(
            user_message="Preciso enviar uma mensagem entre chats usando watcher e command_id",
            force=True,
        )
        check("Contexto operacional aprendido" in context, "context heading missing")
        check("send-chat-message" in context, "context missing interchat lesson")
        check("Nao mencione memoria interna" in context, "context missing confidentiality instruction")

        appended = ctx.append_operational_lesson_context(
            base_context="Base anterior.",
            user_message="Recebi envelope_parse_error no AI_LOCAL",
            force=True,
        )
        check("Base anterior." in appended, "base context missing after append")
        check("envelope" in appended.lower(), "lesson context missing after append")

        no_topic = ctx.build_operational_lesson_context_for_chat(
            user_message="qual a capital da franca?",
            force=True,
        )
        check(no_topic == "", "unrelated message should not receive operational context")

    finally:
        os.environ.clear()
        os.environ.update(old_env)

    print("OK smoke_operational_lesson_context")


if __name__ == "__main__":
    main()
