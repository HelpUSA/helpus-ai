# Local Plan Audit v1

Status: implemented for HelpUSAI Phase C preparation.

## Purpose

The audit layer records plan proposals before any future execution capability exists. It does not approve, schedule, run, or mutate commands.

## Endpoints

- `POST /local/plan/proposals`
- `GET /local/plan/proposals`

## Invariants

Every proposal record keeps:

- `mode = "proposal_only"`
- `version = "local-plan-audit-v1"`
- `executed = false`
- `approved = false`
- `approval_status = "pending_human_review"`
- `requires_human_confirmation = true`

## Storage

Proposal records are stored as JSON Lines in `reports/local-plan-proposals.jsonl`.

The smoke test redirects storage to a temporary file, so validation does not dirty the repository.

## Next gate

Before any execution is introduced, the project should add explicit human approval records, immutable audit entries, proposal-to-approval linking, and keep the executor disabled by default.

## Executor absence guard

The repository includes `scripts/38_smoke_local_executor_absent.py` to prevent accidental introduction of local execution endpoints before the human approval model is designed.

The smoke checks that:

- no `/local/execute`, `/local/commands`, `/local/plan/execute`, `/local/plan/run`, or approval endpoint exists;
- the audit module does not call `subprocess`, `os.system`, `Popen`, `check_call`, or `check_output`;
- proposal records keep `executed=false`, `approved=false`, and `approval_status=pending_human_review`.
