# HelpUS AI operations delta - 2026-06-12

## Current production state

- AI_PROVIDER=deepseek.
- AI_PROVIDER_ORDER=deepseek.
- DEEPSEEK_MODEL=deepseek-chat.
- Backend health and status endpoints returned HTTP 200.
- Status endpoint reported provider_order=[deepseek], provider_configured=deepseek, provider_used=deepseek.
- Production smoke passed using the Vercel frontend URL.

## Frontend domain note

- Official public domain: https://ai.helpusbr.com.
- Functional smoke/local URL: https://helpus-ai.vercel.app.
- ai.helpusbr.com is valid in Vercel and works from mobile data.
- The current local network resolves DNS but cannot connect to Vercel edge IPs on TCP 443.
- Treat this as a local network route/DNS issue until proven otherwise.

## Follow-up

- Rotate Railway secrets that were printed during local diagnostics.
- Keep smoke default on the Vercel URL while the local network issue persists.

