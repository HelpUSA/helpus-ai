import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import helpus_operational_lessons as lessons


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    old_env = dict(os.environ)

    try:
        os.environ.pop(lessons.LESSON_MEMORY_ENABLED_ENV, None)

        lesson = lessons.build_operational_lesson(
            topic="AI Bridge Local Interchat",
            problem="  problema com JSON   e texto extra  ",
            correction="usar envelope puro",
            evidence="evidencia",
            confidence=2,
            tags=["Watcher", "AI Bridge Local", "Watcher"],
        )

        check(lesson.topic == "ai_bridge_local_interchat", "topic normalization failed")
        check(lesson.problem == "problema com JSON e texto extra", "problem cleanup failed")
        check(lesson.confidence == 1.0, "confidence clamp failed")
        check(lesson.tags == ("watcher", "ai_bridge_local"), "tag normalization failed")

        summary = lessons.build_lesson_summary(lesson)
        check("topic=ai_bridge_local_interchat" in summary, "summary missing topic")
        check("correction=usar envelope puro" in summary, "summary missing correction")

        payload = lessons.build_lesson_memory_payload(lesson)
        check(payload["kind"] == "operational_lesson", "payload kind mismatch")
        check(payload["automatic_rule_promotion"] is False, "payload unsafe auto promotion")
        check(payload["requires_validation_before_promotion"] is True, "payload missing validation requirement")

        prompt_text = lessons.format_lessons_for_prompt([lesson], topic="ai_bridge_local_interchat")
        check("Licoes operacionais relevantes" in prompt_text, "prompt formatting missing heading")
        check("usar envelope puro" in prompt_text, "prompt formatting missing correction")

        unrelated = lessons.format_lessons_for_prompt([lesson], topic="outro_topico")
        check(unrelated == "", "prompt should filter unrelated topic")

        parsed = lessons.parse_ai_local_error_to_lesson(
            "[AI_LOCAL_ERRO] tipo=envelope_parse_error erro=JSON invalido",
            topic="ai_bridge_local",
        )
        check(parsed.topic == "ai_bridge_local", "parsed topic mismatch")
        check("JSON invalido" in parsed.evidence, "parsed evidence missing")
        check("Envelope do AI Bridge Local falhou" in parsed.problem, "parse error problem mismatch")
        check("command_id unico" in parsed.correction, "parse error correction missing command_id")

        delivery = lessons.parse_ai_local_error_to_lesson(
            "submit_not_confirmed_composer_still_has_text",
            topic="ai_bridge_local_delivery",
        )
        check("composer" in delivery.problem.lower(), "delivery problem missing composer")
        check("command_id novo" in delivery.correction, "delivery correction missing retry guidance")

        interchat = lessons.watcher_interchat_protocol_lesson()
        check(interchat.topic == "ai_bridge_local_interchat", "interchat topic mismatch")
        check("send-chat-message" in interchat.correction, "interchat correction missing action")
        check("inter_agent_message" in interchat.correction, "interchat correction missing delivery kind")
        check("RECEBIDO_HELPUSAI_SUPERVISOR_009" in interchat.evidence, "interchat evidence missing test marker")

        disabled = lessons.record_operational_lesson_candidate(
            topic="ai_bridge_local",
            problem="p",
            correction="c",
        )
        check(disabled.status == "skipped", "disabled status mismatch")
        check(disabled.enabled is False, "disabled enabled mismatch")
        check(disabled.reason == "operational_lessons_disabled", "disabled reason mismatch")

        os.environ[lessons.LESSON_MEMORY_ENABLED_ENV] = "1"

        enabled = lessons.record_operational_lesson_candidate(
            topic="ai_bridge_local",
            problem="p",
            correction="c",
            conversation_id="smoke-operational-lessons",
        )
        check(enabled.enabled is True, "enabled result should indicate enabled")
        check(enabled.status in {"skipped", "recorded"}, "enabled status invalid")

        status = lessons.recorder_status()
        check(status["enabled"] is True, "status enabled mismatch")
        check(status["automatic_rule_promotion"] is False, "status unsafe auto promotion")

    finally:
        os.environ.clear()
        os.environ.update(old_env)

    print("OK smoke_operational_lessons")


if __name__ == "__main__":
    main()
