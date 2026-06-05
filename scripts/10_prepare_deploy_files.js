const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const backend = path.join(root, "backend");
const frontend = path.join(root, "frontend");

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content.replace(/\r\n/g, "\n"), "utf8");
  console.log("[write]", file);
}

function run(cmd, args, cwd) {
  console.log(`\n[run] ${cmd} ${args.join(" ")}`);
  cp.execFileSync(cmd, args, { cwd, stdio: "inherit", shell: true });
}

write(path.join(root, "railway.json"), `{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
`);

write(path.join(backend, "Procfile"), `web: uvicorn main:app --host 0.0.0.0 --port $PORT
`);

write(path.join(backend, "runtime.txt"), `python-3.14
`);

write(path.join(root, "vercel.json"), `{
  "version": 2,
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs"
}
`);

write(path.join(root, "README_DEPLOY.md"), `# HelpUS - Deploy Vercel + Railway

## Arquitetura

- Frontend: Vercel, pasta \`frontend\`
- Backend: Railway, pasta \`backend\`
- Banco: Railway PostgreSQL
- IA: Gemini API
- Python local/projeto: 3.14
- Node: usar versão compatível com Next 16

## Variáveis do Railway

Configure no serviço do backend:

\`\`\`env
ENVIRONMENT=production
AI_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_gemini
GEMINI_MODEL=gemini-2.5-flash-lite
DATABASE_URL=postgresql://...
\`\`\`

Observação: se usar PostgreSQL criado dentro do Railway, copie a variável \`DATABASE_URL\` gerada pelo Railway.

## Railway

Opção recomendada:

1. Criar novo projeto no Railway.
2. Adicionar PostgreSQL.
3. Adicionar serviço a partir do repositório Git.
4. Definir root/repo com Dockerfile em \`backend/Dockerfile\`.
5. Conferir que o comando de start é:
   \`\`\`bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   \`\`\`

Endpoints esperados:

\`\`\`text
/
 /saude
/status
/chat
\`\`\`

## Variáveis do Vercel

Configure no projeto frontend:

\`\`\`env
NEXT_PUBLIC_API_URL=https://sua-api.up.railway.app
\`\`\`

## Vercel

Opção recomendada:

1. Criar projeto a partir do repositório Git.
2. Definir Root Directory como \`frontend\`.
3. Build Command:
   \`\`\`bash
   npm run build
   \`\`\`
4. Install Command:
   \`\`\`bash
   npm install
   \`\`\`
5. Output: automático do Next.

## Teste local do backend

\`\`\`powershell
cd D:/dev/ai/backend
$env:AI_PROVIDER="gemini"
$env:GEMINI_API_KEY="dummy"
$env:GEMINI_MODEL="gemini-2.5-flash-lite"
./.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
\`\`\`

Em outro terminal:

\`\`\`powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/saude
Invoke-RestMethod http://127.0.0.1:8000/status
\`\`\`

## Teste local do frontend

\`\`\`powershell
cd D:/dev/ai/frontend
npm install
npm run build
npm run dev
\`\`\`

## Observações de segurança

- Não versionar \`.env\`.
- Não versionar modelos \`.gguf\`.
- Não colocar \`GEMINI_API_KEY\` em arquivo público.
- CORS ainda deve ser restringido antes de produção pública.
- O \`npm audit\` pode apontar vulnerabilidade em dependência interna do Next. Não usar \`npm audit fix --force\` se ele tentar rebaixar Next para versão antiga.
`);

const gitignorePath = path.join(root, ".gitignore");
let gitignore = fs.readFileSync(gitignorePath, "utf8");
const additions = [
  "",
  "# Env files",
  "backend/.env",
  "frontend/.env.local",
  "frontend/.env",
  "",
  "# Runtime/build",
  "frontend/.next/",
  "frontend/node_modules/",
  "backend/.venv/",
];
for (const item of additions) {
  if (item && !gitignore.includes(item)) {
    gitignore += "\n" + item;
  }
}
fs.writeFileSync(gitignorePath, gitignore.replace(/\r\n/g, "\n"), "utf8");

run("python", ["-m", "py_compile", "config.py", "banco.py", "cerebro.py", "buscador.py", "main.py"], backend);
run("npm", ["run", "build"], frontend);

console.log("\n[deploy] Deploy files prepared.");
