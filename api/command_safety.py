from dataclasses import dataclass

DESTRUCTIVE_MARKERS = (
    "remove-item",
    " rkdir ",
    " rm ",
    "git reset",
    "git clean",
    "drop database",
    "format ",
)

@dataclass
class CommandSafetyResult:
    allowed: bool
    requires_dry_run: bool
    reason: str = ""


class CommandSafetyPolicy:
    @classmethod
    def command_text(cls, command: list[str]) -> str:
        return " " + " ".join(str(part).lower() for part in command) + " "

    @classmethod
    def requires_dry_run(cls, command: list[str]) -> bool:
        text = cls.command_text(command)
        return any(marker in text for marker in DESTRUCTIVE_MARKERS)

    @classmethod
    def validate(
        cls,
        command: list[str],
        allow_destructive: bool = False,
        dry_run_confirmed: bool = False,
    ) -> CommandSafetyResult:
        if not isinstance(command, list) or not command or any(not str(part).strip() for part in command):
            return CommandSafetyResult(False, False, "command must be a non-empty list")
        needs_dry_run = cls.requires_dry_run(command)
        if needs_dry_run and not (allow_destructive or dry_run_confirmed):
            return CommandSafetyResult(False, True, "destructive command requires dry-run or explicit authorization")
        return CommandSafetyResult(True, needs_dry_run, "ok")
