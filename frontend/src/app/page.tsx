'use client'
import Link from 'next/link'
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

interface ConversaResumo {
  session_id: string
  titulo: string
  updated_at?: string
  total_mensagens: number
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
  const [conversas, setConversas] = useState<ConversaResumo[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''

  const authHeaders = (token = googleToken) => ({
    Authorization: `Bearer ${token}`,
  })

  const carregarConversas = async (token = googleToken) => {
    if (!token) return

    try {
      setHistoryLoading(true)
      const response = await fetch(`${apiUrl}/conversas`, {
        headers: authHeaders(token),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data?.detail || `Erro HTTP ${response.status}`)
      setConversas(data.conversas || [])
    } catch (error) {
      console.error('Erro ao carregar conversas', error)
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    const savedToken = window.localStorage.getItem('helpus_google_token') || ''
    if (savedToken) {
      setGoogleToken(savedToken)
      setProfile(decodeJwtProfile(savedToken))
      carregarConversas(savedToken)
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
        carregarConversas(token)
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
    setConversas([])
    window.localStorage.removeItem('helpus_google_token')
    setMessages([])
    setSessionId('')
  }

  const carregarHistorico = async (id: string) => {
    if (!googleToken) return

    try {
      setLoading(true)
      const response = await fetch(`${apiUrl}/historico/${id}`, {
        headers: authHeaders(),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data?.detail || `Erro HTTP ${response.status}`)

      setSessionId(id)
      setMessages(data.mensagens || [])
      setSidebarOpen(false)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Erro ao carregar historico: ${message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  const apagarConversa = async (id: string) => {
    if (!googleToken) return
    const confirmar = window.confirm('Apagar esta conversa?')
    if (!confirmar) return

    try {
      const response = await fetch(`${apiUrl}/conversa/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data?.detail || `Erro HTTP ${response.status}`)

      if (sessionId === id) {
        setMessages([])
        setSessionId('')
      }
      await carregarConversas()
      setSidebarOpen(false)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      alert(`Erro ao apagar conversa: ${message}`)
    }
  }

  const enviarMensagem = async () => {
    const texto = input.trim()
    if (!texto || loading) return

    if (!googleToken) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Entre com sua conta Google para usar o HelpUS.' },
      ])
      return
    }

    setMessages(prev => [...prev, { role: 'user', content: texto }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${googleToken}`,
        },
        body: JSON.stringify({
          mensagem: texto,
          session_id: sessionId || undefined,
          pesquisar_web: pesquisarWeb,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const detail = data?.detail || `Erro HTTP ${response.status}`
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

      await carregarConversas()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Erro ao conectar com o servidor: ${message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  const limparChat = () => {
    setMessages([])
    setSessionId('')
    setInput('')
    setSidebarOpen(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      enviarMensagem()
    }
  }

  return (
    <main className="min-h-screen bg-white text-slate-900">
      <Script src="https://accounts.google.com/gsi/client" async defer onLoad={inicializarGoogle} />

      <div className="flex min-h-screen w-full flex-col">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 px-3 py-2 backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">HelpUS</h1>
                <p className="text-sm text-slate-500">Seu HelpUS Inteligente</p>
              </div>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 lg:hidden"
              >
                Historico
              </button>
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

              <Link
                href="/admin"
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
              >
                Admin
              </Link>

              <button
                onClick={limparChat}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
                title="Limpar conversa"
              >
                Nova conversa
              </button>
            </div>
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <aside
            className={`${sidebarOpen ? 'block' : 'hidden'} w-full border-r border-zinc-800 bg-zinc-950 p-3 text-zinc-100 lg:block lg:w-72`}
          >
            <div className="mb-3 flex items-center justify-between gap-2">
              <h2 className="font-semibold text-zinc-100">Minhas conversas</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="rounded-lg border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:bg-zinc-800 lg:hidden"
                >
                  Voltar ao chat
                </button>
                <button
                  onClick={() => carregarConversas()}
                  disabled={!profile || historyLoading}
                  className="rounded-lg border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
                >
                  Atualizar
                </button>
              </div>
            </div>

            <button
              onClick={limparChat}
              className="mb-3 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm font-medium text-zinc-100 transition hover:bg-zinc-800"
            >
              Nova conversa
            </button>

            {!profile && (
              <p className="rounded-lg bg-zinc-900 p-3 text-sm text-zinc-300">
                Entre com Google para ver seu histórico.
              </p>
            )}

            {profile && conversas.length === 0 && (
              <p className="rounded-lg bg-zinc-900 p-3 text-sm text-zinc-400">
                Nenhuma conversa salva ainda.
              </p>
            )}

            <div className="space-y-2">
              {conversas.map((conv) => (
                <div
                  key={conv.session_id}
                  className={`group rounded-xl border p-3 transition hover:bg-zinc-800 ${
                    sessionId === conv.session_id
                      ? 'border-zinc-600 bg-zinc-800'
                      : 'border-transparent bg-zinc-900'
                  }`}
                >
                  <button
                    onClick={() => carregarHistorico(conv.session_id)}
                    className="block w-full text-left"
                  >
                    <div className="truncate text-sm font-medium text-zinc-100">
                      {conv.titulo || 'Nova conversa'}
                    </div>
                    <div className="mt-1 text-xs text-zinc-400">
                      {conv.total_mensagens} mensagens
                    </div>
                  </button>
                  <button
                    onClick={() => apagarConversa(conv.session_id)}
                    className="mt-2 text-xs font-medium text-zinc-500 opacity-80 hover:text-red-300 group-hover:opacity-100"
                  >
                    Apagar
                  </button>
                </div>
              ))}
            </div>
          </aside>

          <section className="flex min-w-0 flex-1 flex-col">
            <div className="flex-1 overflow-y-auto px-4 py-6">
              {messages.length === 0 && (
                <div className="mx-auto mt-16 max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                  <p className="text-3xl font-bold text-slate-900">Como posso ajudar?</p>
                  <p className="mt-3 text-slate-500">
                    Entre com Google e pergunte algo ao HelpUS.
                  </p>
                  {!profile && (
                    <p className="mt-4 rounded-lg bg-zinc-900 p-3 text-sm text-zinc-300">
                      Entre com Google para iniciar uma conversa segura com o HelpUS.
                    </p>
                  )}
                  <div className="mt-8 grid gap-3 text-left text-sm text-slate-700 sm:grid-cols-2">
                    <button
                      onClick={() => setInput('Quem é você?')}
                      className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow-md"
                    >
                      Quem é você?
                    </button>
                    <button
                      onClick={() => setInput('Explique em poucas palavras como o HelpUS funciona.')}
                      className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow-md"
                    >
                      Como funciona?
                    </button>
                  </div>
                </div>
              )}

              <div className="space-y-5">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <article
                      className={`max-w-[92%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[78%] ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'border border-slate-200 bg-white text-slate-900'
                      }`}
                    >
                      <div className={`mb-1 text-sm font-bold ${msg.role === 'user' ? 'text-blue-50' : 'text-slate-900'}`}>
                        {msg.role === 'user' ? 'Voce' : 'HelpUS'}
                      </div>

                      <div className="whitespace-pre-wrap text-[15px] leading-7 text-slate-800 sm:text-base">
                        {msg.content}
                      </div>

                      {msg.role === 'assistant' && (
                        <button
                          type="button"
                          onClick={() => navigator.clipboard?.writeText(msg.content)}
                          className="mt-3 rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
                        >
                          Copiar
                        </button>
                      )}

                      {msg.fontes && msg.fontes.length > 0 && (
                        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
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
                                className="block truncate text-sm text-slate-700 hover:text-slate-950 hover:underline"
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
                    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm shadow-slate-100">
                      <div className="flex items-center gap-3 text-sm text-slate-500">
                        <div className="flex gap-1">
                          <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400"></span>
                          <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400"></span>
                          <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400"></span>
                        </div>
                        HelpUS está pensando...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <footer className="bg-white px-4 pb-5 pt-3">
              <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg shadow-slate-200/70">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={profile ? 'Pergunte alguma coisa ao HelpUS' : 'Entre com Google para usar o HelpUS'}
                  className="min-h-[44px] flex-1 resize-none rounded-xl border-0 bg-transparent p-3 text-sm outline-none placeholder:text-slate-400"
                  rows={1}
                  disabled={loading || !profile}
                />
                <button
                  onClick={enviarMensagem}
                  disabled={loading || !input.trim() || !profile}
                  className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40 sm:px-6"
                >
                  {loading ? '...' : 'Enviar'}
                </button>
              </div>

              {sessionId && (
                <p className="mx-auto mt-2 max-w-3xl text-xs text-slate-400">
                  Sessao: {sessionId.slice(0, 8)}...
                </p>
              )}
            </footer>
          </section>
        </div>
      </div>
    </main>
  )
}
