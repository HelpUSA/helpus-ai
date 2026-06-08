const rawBase = process.env.HELPUS_API_URL || 'https://helpus-api-production.up.railway.app ';
const base = rawBase.trim().endsWith('/') ? rawBase.trim().slice(0, -1) : rawBase.trim();
const token = process.env.HELPUS_GOOGLE_ID_TOKEN || '';
if (!token) {
 console.log('CHAT_SMOKE_SKIPPED_AUTH_REQUIRED');
 process.exit(0);
}
const body = JSON.stringify({mensagem:'Teste rapido de saude do chat. Responda apenas OK.', pesquisar_web:false});
fetch(base + '/chat', {method:'POST', headers:{'Content-Type':'application/json', Authorization:'Bearer ' + token}, body})
 .then(async r => {
 const text = await r.text();
 console.log('CHAT_STATUS', r.status);
 console.log(text.slice(0, 500));
 if (!r.ok) process.exit(1);
 const parsed = JSON.parse(text);
 if (!parsed.resposta || !parsed.session_id) process.exit(1);
 console.log('HELPUS_CHAT_SMOKE_OK');
 })
 .catch(e => { console.error(e.message); process.exit(1); });
