const A=process.env.HELPUS_API_URL||'https://helpus-api-production.up.railway.app';
const W=process.env.HELPUS_FRONTEND_URL||'https://helpus-ai.vercel.app';
async function j(u){const r=await fetch(u); if(!r.ok) throw Error(u+' '+r.status); return r.json()}
async function h(u){const r=await fetch(u); if(!r.ok) throw Error(u+' '+r.status); return r.status}
function ok(n,c){if(!c) throw Error(n); console.log('OK '+n)}
(async()=>{const s=await j(A+'/saude'); ok('saude',s.status==='saudavel'&&s.modelo_ok===true); const t=await j(A+'/status'); ok('status',t.status==='online'&&t.modelo_carregado===true&&Number.isInteger(t.paginas_indexadas)); const f=await h(W+'/'); ok('front',f>=200&&f<400); const a=await h(W+'/admin'); ok('admin',a>=200&&a<400); console.log('HELPUS_SMOKE_OK')})().catch(e=>{console.error(e);process.exit(1)});
