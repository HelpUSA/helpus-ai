# HelpUS AI operational closure - 2026-06-12

## Validation completed

- Railway backend is online.
- Health endpoint /saude returned saudavel.
- Status endpoint returned online.
- Provider configured and used is deepseek.
- Active model is deepseek-chat.
- Internal smoke chat with token returned HTTP 200 using deepseek.
- Production smoke passed using the Vercel frontend URL.
- Frontend build passed.

## Domain note

- ai.helpusbr.com is valid in Vercel and works from mobile data.
- The local network resolves DNS but cannot connect to Vercel edge IPs on TCP 443.
- This is a local network or route issue, not a HelpUS backend, DeepSeek, or Vercel app issue.
- Until the local route is recovered, use the Vercel URL for smoke validation.

## Security note

- Rotate exposed operational secrets after this session because Railway variables were printed in a local command output.

## Current git reference

- Last relevant code commit: 74c61bf Enable HelpUS provider loop for DeepSeek primary.

