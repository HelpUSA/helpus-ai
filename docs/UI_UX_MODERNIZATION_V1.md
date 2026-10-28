# HelpUS AI — UI/UX Modernization v1

Implementation branch: `feature/ui-ux-modernization-v1`.
Baseline: current `main` — no production changes.

## Scope and acceptance
1. Responsive shell with 280px desktop sidebar and accessible mobile drawer (backdrop, Escape, focus return), keyboard shortcut Ctrl+B, clear navigation landmarks.
2. Conversation history grouped by date (Today, Yesterday, 7 days, Older) using local timezone; project selector, search, and empty states. Keep server as source of truth; local cache is provisional.
3. Model selector must reflect **actual backend capabilities**. Do not send an unimplemented `model_alias` or silently ignore choice. Backend validation must allowlisted aliases and enforce provider availability.
4. Composer: autosizing textbox; Enter to send, Shift+Enter for new line; thumbnail/file chip with removal; drag-drop, keyboard-accessible file picker, MIME/size checks; no secrets in uploads or logs.
5. SSE: partial Markdown updates without duplicate chunks, visibly streaming status, AbortController cancellation, retry only with user action, differentiated timeout/401/429/5xx UI and an actionable nontechnical message.
6. Provider metadata is **only displayed when server-verified**. Never label static fallback as an AI model reply.
7. Visual language: original HelpUS identity, restrained dark palette, readable text (WCAG AA), unified spacing, mobile-first layout, crisp message hierarchy and reduced-motion option.
8. No local-computer command dispatch from web chat. Auth and tenant isolation are blockers before cloud-history rollout.

## Quality gates
- Unit tests: grouping including timezone boundaries, upload validation, model selector mapping, cancellation, retry behavior.
- Integration: successful SSE, static fallback, provider error, timeout, network disconnect, logged-out state, permission denial, cross-project isolation.
- Browser: keyboard navigation, screen reader semantics, responsive at 360 / 768 / 1280 pixels, visual regression and no hydration errors.
- Coordinate with PR #1 to avoid merging a vulnerable `main`; rebase security hardening after integration tests pass.
- No deploy or migrations without green checks and a documented rollback.

## Collaboration
Antigravity: implement UI components locally on this isolated branch/worktree; commit atomic pieces, attach screenshots and test logs. ChatGPT: review diffs, architecture and regression checks before merge. Communicate concrete blockers with SHA and target file; do not silently modify production.
