const assert = require('assert')

// Simulamos ambiente ou importamos compilado
const { resolveApiUrl } = require('./resolveApiUrl.ts')

// Testa casos de fallback seguro
assert.strictEqual(resolveApiUrl({ rawUrl: '' }), '', 'Empty string should resolve to local API ""')
assert.strictEqual(resolveApiUrl({ rawUrl: '  ' }), '', 'Whitespace should resolve to local API ""')
assert.strictEqual(resolveApiUrl({ rawUrl: '/' }), '', 'Slash should resolve to local API ""')
assert.strictEqual(resolveApiUrl({ rawUrl: 'auto' }), '', '"auto" should resolve to local API ""')
assert.strictEqual(resolveApiUrl({ rawUrl: 'local' }), '', '"local" should resolve to local API ""')

// Testa flag forçada
assert.strictEqual(resolveApiUrl({ rawUrl: 'https://example.com', forceLocal: true }), '', 'forceLocal=true must override rawUrl to ""')

// Testa remoção de Railway legada
assert.strictEqual(resolveApiUrl({ rawUrl: 'https://helpus-api-production.up.railway.app' }), '', 'Railway host must be neutralized to ""')
assert.strictEqual(resolveApiUrl({ rawUrl: 'https://another-app.railway.app/' }), '', 'Any railway.app host must be neutralized to ""')

// Testa rotas relativas válidas
assert.strictEqual(resolveApiUrl({ rawUrl: '/api' }), '/api', 'Relative path /api should be preserved')

// Testa URL externa legítima com trailing slash removida
assert.strictEqual(resolveApiUrl({ rawUrl: 'https://api.external.com/api/' }), 'https://api.external.com/api', 'External URL trailing slashes should be trimmed')

// Testa se coincide com a origem atual do navegador
assert.strictEqual(resolveApiUrl({ rawUrl: 'https://ai.helpusbr.com', currentOrigin: 'https://ai.helpusbr.com' }), '', 'Matching origin should resolve to relative ""')

console.log('ALL RESOLVE API URL TESTS PASSED!')
