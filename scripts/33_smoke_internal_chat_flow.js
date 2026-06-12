const rawBase = process.env.HELPUS_API_URL || 'https://helpus-api-production.up.railway.app'
const base = rawBase.trim().endsWith('/') ? rawBase.trim().slice(0, -1) : rawBase.trim()
const token = process.env.HELPUS_INTERNAL_SMOKE_TOKEN || ''

if (!token) {
  console.error('HELPUS_INTERNAL_SMOKE_TOKEN missing')
  process.exit(1)
}

async function post(headers) {
  return fetch(base + '/internal/smoke-chat-auth-flow', {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, headers || {}),
    body: '{}',
  })
}

async function main() {
  const noToken = await post({})
  console.log('NO_TOKEN_STATUS', noToken.status)
  if (noToken.status !== 401) throw new Error('Expected 401 without internal token')

  const response = await post({ 'x-internal-smoke-token': token })
  const text = await response.text()
  console.log('INTERNAL_CHAT_STATUS', response.status)
  if (!response.ok) {
    console.log(text.slice(0, 500))
    throw new Error('Internal chat flow failed')
  }
  const parsed = JSON.parse(text)
  if (!parsed.resposta || !parsed.session_id) throw new Error('Missing resposta/session_id')
  if (parsed.provider_used && parsed.provider_used !== 'deepseek') throw new Error('Unexpected provider_used ' + parsed.provider_used)
  console.log('SESSION_ID_PRESENT', Boolean(parsed.session_id))
  console.log('PROVIDER_USED', parsed.provider_used || 'not_reported')
  console.log('MODEL', parsed.model || 'not_reported')
  console.log('HELPUS_INTERNAL_CHAT_FLOW_SMOKE_OK')
}

main().catch(error => {
  console.error(error.message)
  process.exit(1)
})
