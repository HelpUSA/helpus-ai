'use client'
import Link from 'next/link'
import Script from 'next/script'
import { useEffect, useState } from 'react'

interface ApiStatus {
  status?: string
  modelo?: string
  modelo_carregado?: boolean
  paginas_indexadas?: number
}

interface ApiSaude {
  status?: string
  modelo_ok?: boolean
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

export default function AdminPage() {
  const appVersion = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'
  const appCommit = process.env.NEXT_PUBLIC_APP_COMMIT || 'local'
  const [saude, setSaude] = useState<ApiSaude | null>(null)
  const [status, setStatus] = useState<ApiStatus | null>(null)
  const [profile, setProfile] = useState<GoogleProfile | null>(null)
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''

  useEffect(() => {
    const savedToken = window.localStorage.getItem('helpus_google_token') || ''
    if (savedToken) {
      setProfile(decodeJwtProfile(savedToken))
    }
    carregarStatus()
  }, [])

  const inicializarGoogle = () => {
    if (!googleClientId || !window.google?.accounts?.id) return

    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: (response: any) => {
        const token = response.credential || ''
        window.localStorage.setItem('helpus_google_token', token)
        setProfile(decodeJwtProfile(token))
      },
    })

    window.google.accounts.id.renderButton(
      document.getElementById('google-login-button-admin'),
      {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'pill',
      }
    )
  }

  const sair = () => {
    window.localStorage.removeItem('helpus_google_token')
    setProfile(null)
  }

  const carregarStatus = async () => {
    try {
      setLoading(true)
      setErro('')

      const [saudeResp, statusResp] = await Promise.all([
        fetch(`${apiUrl}/saude`),
        fetch(`${apiUrl}/status`),
      ])

      const saudeData = await saudeResp.json().catch(() => ({}))
      const statusData = await statusResp.json().catch(() => ({}))

      if (!saudeResp.ok) throw new Error(saudeData?.detail || `Erro /saude: ${saudeResp.status}`)
      if (!statusResp.ok) throw new Error(statusData?.detail || `Erro /status: ${statusResp.status}`)

      setSaude(saudeData)
      setStatus(statusData)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#212121] text-zinc-100">
      <Script src="https://accounts.google.com/gsi/client" async defer onLoad={inicializarGoogle} />

      <div className="mx-auto max-w-5xl px-3 py-4 sm:px-4 sm:py-6">
        <header className="mb-5 flex flex-col gap-4 rounded-3xl border border-white/10 bg-[#2f2f2f] p-4 shadow-2xl shadow-black/20 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold">HelpUS Admin</h1>
            <p className="text-sm text-zinc-400">Status do assistente e serviços conectados</p>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Versao {appVersion} · commit {appCommit}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/"
              className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-zinc-200 hover:bg-white/10"
            >
              Voltar ao chat
            </Link>

            {profile ? (
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200">
                {profile.picture && <img src={profile.picture} alt={profile.name} className="h-6 w-6 rounded-full" />}
                <span className="max-w-[180px] truncate">{profile.name}</span>
                <button onClick={sair} className="font-semibold text-red-500 hover:text-red-700">
                  Sair
                </button>
              </div>
            ) : (
              <div id="google-login-button-admin" />
            )}
          </div>
        </header>

        {erro && (
          <div className="mb-4 rounded-xl border border-red-500/30 bg-red-950/40 p-4 text-sm text-red-200">
            {erro}
          </div>
        )}

        <div className="mb-4 flex justify-end">
          <button
            onClick={carregarStatus}
            disabled={loading}
            className="rounded-full bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-white disabled:opacity-50"
          >
            {loading ? 'Atualizando...' : 'Atualizar status'}
          </button>
        </div>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-white/10 bg-[#2f2f2f] p-5 shadow-2xl shadow-black/20">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">API</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-50">
              {saude?.status || 'Indisponivel'}
            </p>
            <p className="mt-2 text-sm text-zinc-400">
              Modelo OK: {saude?.modelo_ok ? 'sim' : 'nao'}
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#2f2f2f] p-5 shadow-2xl shadow-black/20">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Modelo</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-50">
              {status?.modelo || '-'}
            </p>
            <p className="mt-2 text-sm text-zinc-400">
              Carregado: {status?.modelo_carregado ? 'sim' : 'nao'}
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#2f2f2f] p-5 shadow-2xl shadow-black/20">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Indexacao</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-50">
              {status?.paginas_indexadas ?? 0}
            </p>
            <p className="mt-2 text-sm text-zinc-400">
              paginas indexadas no backend
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#2f2f2f] p-5 shadow-2xl shadow-black/20">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Usuario</p>
            <p className="mt-2 text-xl font-bold text-zinc-50">
              {profile?.name || 'Nao logado'}
            </p>
            <p className="mt-2 truncate text-sm text-zinc-400">
              {profile?.email || 'Entre com Google para identificar o operador.'}
            </p>
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-white/10 bg-[#2f2f2f] p-5 shadow-2xl shadow-black/20">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Endpoints</p>
          <div className="mt-3 grid gap-2 text-sm text-zinc-300 sm:grid-cols-2">
            <code className="rounded-xl border border-white/10 bg-zinc-950 p-3 text-zinc-100">GET /saude</code>
            <code className="rounded-xl border border-white/10 bg-zinc-950 p-3 text-zinc-100">GET /status</code>
            <code className="rounded-xl border border-white/10 bg-zinc-950 p-3 text-zinc-100">POST /chat</code>
            <code className="rounded-xl border border-white/10 bg-zinc-950 p-3 text-zinc-100">GET /conversas</code>
          </div>
        </section>
      </div>
    </main>
  )
}
