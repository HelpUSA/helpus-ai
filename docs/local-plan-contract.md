# Local Plan Contract v1

Status: implemented for HelpUSAI Phase B.

## Purpose

`POST /local/plan` classifies local operator requests without executing commands. It is a planning contract only.

## Endpoints

- `POST /local/plan`
- `GET /local/plan/intents`

## Invariants

Every plan response must keep:

- `mode = "plan_only"`
- `version = "local-plan-v1"`
- `executed = false`
- `requires_human_confirmation = true`

## Result classes

- `readonly`: command is allowlisted for planning, but still not executed.
- `needs_review`: command is not explicitly allowlisted and must be reviewed by a human.
- `blocked`: destructive tokens, dangerous separators, too many commands, or oversized commands were detected.
- `unknown`: no known intent or command was provided.

## Known intents

- `phase_a_validation`
- `phase_b_validation`
- `local_status`
- `local_diff`
- `local_recent_commits`
- `local_api_smoke`
- `admin_local_smoke`
- `build`

## Limits

- Maximum commands per request: 5
- Maximum command length: 240 characters
- Dangerous separators are blocked: `&&`, `||`, `;`, backticks, `$(`, `>`, `<`
- Destructive/local mutation/deploy tokens are blocked, including `git push`, `git commit`, `git add`, `git reset`, `git clean`, removals, deploy commands and remote download commands.

## UI behavior

`/admin/local` may call the planner and display the classification. The UI must not offer an execute button in Phase B.
