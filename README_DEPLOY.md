# HelpUS - Deploy Vercel + Railway

## Arquitetura

- Frontend: Vercel, pasta `frontend`
- Backend: Railway, pasta `backend`
- Banco: Railway PostgreSQL
- IA: Gemini API
- Python local/projeto: 3.14
- Node: usar versão compatível com Next 16

## Variáveis do Railway

Configure no serviço do backend:

```env
ENVIRONMENT=production
AI_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_gemini
GEMINI_MODEL=gemini-2.5-flash-lite
DATABASE_URL=postgresql://...
```

Observação: se usar PostgreSQL criado dentro do Railway, copie a variável `DATABASE_URL` gerada pelo Railway.

## Railway

Opção recomendada:

1. Criar novo projeto no Railway.
2. Adicionar PostgreSQL.
3. Adicionar serviço a partir do repositório Git.
4. Definir root/repo com Dockerfile em `backend/Dockerfile`.
5. Conferir que o comando de start é:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

Endpoints esperados:

```text
/
 /saude
/status
/chat
```

## Variáveis do Vercel

Configure no projeto frontend:

```env
NEXT_PUBLIC_API_URL=https://sua-api.up.railway.app
```

## Vercel

Opção recomendada:

1. Criar projeto a partir do repositório Git.
2. Definir Root Directory como `frontend`.
3. Build Command:
   ```bash
   npm run build
   ```
4. Install Command:
   ```bash
   npm install
   ```
5. Output: automático do Next.

## Teste local do backend

```powershell
cd D:/dev/ai/backend
$env:AI_PROVIDER="gemini"
$env:GEMINI_API_KEY="dummy"
$env:GEMINI_MODEL="gemini-2.5-flash-lite"
./.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Em outro terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/saude
Invoke-RestMethod http://127.0.0.1:8000/status
```

## Teste local do frontend

```powershell
cd D:/dev/ai/frontend
npm install
npm run build
npm run dev
```

## Observações de segurança

- Não versionar `.env`.
- Não versionar modelos `.gguf`.
- Não colocar `GEMINI_API_KEY` em arquivo público.
- CORS ainda deve ser restringido antes de produção pública.
- O `npm audit` pode apontar vulnerabilidade em dependência interna do Next. Não usar `npm audit fix --force` se ele tentar rebaixar Next para versão antiga.
