# HelpUS AI operational status - 2026-06-12

## Closed validation

- Backend Railway is online.
- Health endpoint /saude returns saudavel.
- Status endpoint reports provider configured/used as deepseek.
- Active model is deepseek-chat.
- Internal smoke chat with token returned HTTP 200 and provider_used=deepseek.
- Production smoke passed with the Vercel frontend URL.
- Frontend build passed.

## Domain note

- ai.helpusbr.com is valid in Vercel and worked from mobile data.
- The local network could resolve DNS but could not connect to the Vercel edge IPs on port 443.
- This is tracked as a local network/route/DNS issue, not a backend or application issue.
- Until the local route is recovered, use https://helpus-ai.vercel.app for smoke validation.

## Git reference

- Last relevant commit: 74c61bf Enable HelpUS provider loop for DeepSeek primary.

