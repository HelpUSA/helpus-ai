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

function run(command, cwd) {
  console.log("\n[run] " + command);
  cp.execSync(command, { cwd, stdio: "inherit", shell: true });
}

// Backend requirements
const reqPath = path.join(backend, "requirements.txt");
let req = fs.readFileSync(reqPath, "utf8");
if (!req.includes("google-auth")) {
  req = req.trimEnd() + "\ngoogle-auth>=2.23.0,<3.0.0\n";
  fs.writeFileSync(reqPath, req, "utf8");
}

// Backend config
const configPath = path.join(backend, "config.py");
let config = fs.readFileSync(configPath, "utf8");

if (!config.includes("AUTH_REQUIRED")) {
  config += `

AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower().strip() in ("1", "true", "yes", "on")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
`;
}

write(configPath, config);

// Backend auth.py
write(path.join(backend, "auth.py"), `# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any

from fastapi import Header, HTTPException

from config import AUTH_REQUIRED, GOOGLE_CLIENT_ID


def verificar_google_id_token(token: str) -> Dict[str, Any]:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID nao configurado.")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests

        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token Google invalido.")

    email = info.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token Google sem email.")

    return {
        "sub": info.get("sub"),
        "email": email,
        "name": info.get("name") or email,
        "picture": info.get("picture") or "",
    }


async def obter_usuario_google(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    if not AUTH_REQUIRED:
        return None

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Login Google obrigatorio.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente.")

    return verificar_google_id_token(token)
`);

// Backend main.py patch
const mainPath = path.join(backend, "main.py");
let main = fs.readFileSync(mainPath, "utf8");

main = main.replace(
  "from fastapi import FastAPI, HTTPException",
  "from fastapi import FastAPI, HTTPException, Depends"
);

if (!main.includes("from auth import obter_usuario_google")) {
  main = main.replace(
    "from buscador import MotorBusca",
    "from buscador import MotorBusca\nfrom auth import obter_usuario_google"
  );
}

main = main.replace(
  "async def chat(request: MensagemRequest):",
  "async def chat(request: MensagemRequest, usuario = Depends(obter_usuario_google)):"
);

write(mainPath, main);

// Frontend page.tsx with Google login
write(path.join(frontend, "src/app/page.tsx"), `'use client'
import Script from 'next/script'
import { useEffect, useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  fontes?: { titulo: string; url: string; fonte: string }[]
}

interface GoogleProfile {
  email: string
  name: string
  picture: string
}

declare global {
  interface Window {
    google?: any
  }
}

function decodeJwtProfile(token: string): GoogleProfile | null {
  try {
    const payload = token.split('.')[1]
    const json = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return {
      email: json.email || '',
      name: json.name || json.email || 'Usuario',
      picture: json.picture || '',
    }
  } catch {
    return null
  }
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [pesquisarWeb, setPesquisarWeb] = useState(false)
  const [googleToken, setGoogleToken] = useState('')
  const [profile, setProfile] = useState<GoogleProfile | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''

  useEffect(() => {
    const savedToken = window.localStorage.getItem('helpus_google_token') || ''
    if (savedToken) {
      setGoogleToken(savedToken)
      setProfile(decodeJwtProfile(savedToken))
    }
  }, [])

  const inicializarGoogle = () => {
    if (!googleClientId || !window.google?.accounts?.id) return

    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: (response: any) => {
        const token = response.credential || ''
        const decoded = decodeJwtProfile(token)
        setGoogleToken(token)
        setProfile(decoded)
        window.localStorage.setItem('helpus_google_token', token)
      },
    })

    window.google.accounts.id.renderButton(
      document.getElementById('google-login-button'),
      {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'pill',
      }
    )
  }

  const sair = () => {
    setGoogleToken('')
    setProfile(null)
    window.localStorage.removeItem('helpus_google_token')
    setMessages([])
    setSessionId('')
  }

  const enviarMensagem = async () => {
    const texto = input.trim()
    if (!texto || loading) return

    if (!googleToken) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Entre com sua conta Google para usar o HelpUS.',
        },
      ])
      return
    }

    setMessages(prev => [...prev, { role: 'user', content: texto }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(\`\${apiUrl}/chat\`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: \`Bearer \${googleToken}\`,
        },
        body: JSON.stringify({
          mensagem: texto,
          session_id: sessionId || undefined,
          pesquisar_web: pesquisarWeb,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const detail = data?.detail || \`Erro HTTP \${response.status}\`
        throw new Error(String(detail))
      }

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.resposta || 'A API respondeu sem conteudo.',
          fontes: data.fontes || [],
        },
      ])
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: \`Erro ao conectar com o servidor: \${message}\`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const limparChat = () => {
    setMessages([])
    setSessionId('')
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      enviarMensagem()
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <Script src="https://accounts.google.com/gsi/client" async defer onLoad={inicializarGoogle} />

      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">HelpUS</h1>
              <p className="text-sm text-slate-500">Seu Assistente Inteligente</p>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-sm">
              <label className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={pesquisarWeb}
                  onChange={(e) => setPesquisarWeb(e.target.checked)}
                  className="h-4 w-4 rounded"
                />
                Pesquisar na web
              </label>

              {profile ? (
                <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2">
                  {profile.picture && (
                    <img src={profile.picture} alt={profile.name} className="h-6 w-6 rounded-full" />
                  )}
                  <span className="max-w-[160px] truncate text-slate-700">{profile.name}</span>
                  <button onClick={sair} className="font-semibold text-slate-500 hover:text-red-600">
                    Sair
                  </button>
                </div>
              ) : (
                <div id="google-login-button" />
              )}

              <button
                onClick={limparChat}
                className="rounded-full border border-slate-200 bg-white px-4 py-2 font-medium text-slate-600 transition hover:border-red-200 hover:text-red-600"
                title="Limpar conversa"
              >
                Nova conversa
              </button>
            </div>
          </div>
        </header>

        <section className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 && (
            <div className="mx-auto mt-16 max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <p className="text-3xl font-bold text-slate-900">Como posso ajudar?</p>
              <p className="mt-3 text-slate-500">
                Entre com Google e pergunte algo ao HelpUS.
              </p>
              {!profile && (
                <p className="mt-4 rounded-xl bg-blue-50 p-3 text-sm text-blue-700">
                  Login Google obrigatorio para usar o assistente.
                </p>
              )}
              <div className="mt-6 grid gap-2 text-left text-sm text-slate-600 sm:grid-cols-2">
                <button
                  onClick={() => setInput('Quem e voce?')}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-left hover:bg-slate-100"
                >
                  Quem e voce?
                </button>
                <button
                  onClick={() => setInput('Explique em poucas palavras como este assistente funciona.')}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-left hover:bg-slate-100"
                >
                  Como funciona?
                </button>
              </div>
            </div>
          )}

          <div className="space-y-5">
            {messages.map((msg, index) => (
              <div key={index} className={\`flex \${msg.role === 'user' ? 'justify-end' : 'justify-start'}\`}>
                <article
                  className={\`max-w-[92%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[78%] \${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'border border-slate-200 bg-white text-slate-900'
                  }\`}
                >
                  <div className={\`mb-1 text-sm font-bold \${msg.role === 'user' ? 'text-blue-50' : 'text-slate-900'}\`}>
                    {msg.role === 'user' ? 'Voce' : 'Assistente'}
                  </div>

                  <div className="whitespace-pre-wrap text-sm leading-7 sm:text-base">
                    {msg.content}
                  </div>

                  {msg.fontes && msg.fontes.length > 0 && (
                    <div className="mt-4 border-t border-slate-200 pt-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Fontes consultadas
                      </p>
                      <div className="space-y-1">
                        {msg.fontes.map((fonte, i) => (
                          <a
                            key={i}
                            href={fonte.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block truncate text-sm text-blue-600 hover:underline"
                          >
                            {i + 1}. {fonte.titulo} ({fonte.fonte})
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-3 text-sm text-slate-500">
                    <div className="flex gap-1">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400"></span>
                      <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400"></span>
                      <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400"></span>
                    </div>
                    Pensando...
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        <footer className="sticky bottom-0 border-t border-slate-200 bg-white p-4">
          <div className="mx-auto flex max-w-6xl gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={profile ? "Digite sua pergunta... Enter para enviar" : "Entre com Google para usar o HelpUS"}
              className="min-h-[48px] flex-1 resize-none rounded-xl border border-slate-300 p-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              rows={1}
              disabled={loading || !profile}
            />
            <button
              onClick={enviarMensagem}
              disabled={loading || !input.trim() || !profile}
              className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 sm:px-7"
            >
              {loading ? '...' : 'Enviar'}
            </button>
          </div>

          {sessionId && (
            <p className="mx-auto mt-2 max-w-6xl text-xs text-slate-400">
              Sessao: {sessionId.slice(0, 8)}...
            </p>
          )}
        </footer>
      </div>
    </main>
  )
}
`);

// Frontend env example
write(path.join(frontend, ".env.example"), `NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
`);

// Validate
run("python -m py_compile config.py banco.py cerebro.py buscador.py auth.py main.py", backend);
run("npm run build", root);

console.log("[auth] Google login/auth patch OK");
