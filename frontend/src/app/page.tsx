'use client'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
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
  created_at?: string
  createdAt?: string
  updatedAt?: string
  data?: string
  total_mensagens: number
}

declare global {
  interface Window {
    google?: any
  }
}

function renderInlineMarkdown(text: string) {
  return text.split(/(`[^`]+`)/g).map((part, index) =>
    part.startsWith('`') && part.endsWith('`')
      ? <code key={index} className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px] text-slate-800">{part.slice(1, -1)}</code>
      : <span key={index}>{part}</span>
  )
}

function renderMessageContent(content: string) {
  const lines = content.split('\n')
  const blocks: JSX.Element[] = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]

    if (line.trim().startsWith('```')) {
      index += 1
      const code: string[] = []
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        code.push(lines[index])
        index += 1
      }
      if (index < lines.length) index += 1
      blocks.push(
        <pre key={blocks.length} className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-sm text-slate-100">
          <code>{code.join('\n')}</code>
        </pre>
      )
      continue
    }

    if (line.trim().startsWith('- ')) {
      const items: string[] = []
      while (index < lines.length && lines[index].trim().startsWith('- ')) {
        items.push(lines[index].trim().slice(2))
        index += 1
      }
      blocks.push(
        <ul key={blocks.length} className="list-disc space-y-1 pl-6">
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInlineMarkdown(item)}</li>
          ))}
        </ul>
      )
      continue
    }

    if (line.trim() === '') {
      index += 1
      continue
    }

    const paragraph: string[] = [line]
    index += 1
    while (
      index < lines.length &&
      lines[index].trim() !== '' &&
      !lines[index].trim().startsWith('- ') &&
      !lines[index].trim().startsWith('```')
    ) {
      paragraph.push(lines[index])
      index += 1
    }

    blocks.push(
      <p key={blocks.length}>{renderInlineMarkdown(paragraph.join(' '))}</p>
    )
  }

  return <div className="space-y-4 text-[15px] leading-7 text-slate-800 sm:text-base">{blocks}</div>
}


function tituloConversa(conv: ConversaResumo) {
  const titulo = (conv.titulo || '').trim()
  if (titulo && titulo !== 'Nova conversa') return titulo
  return `Conversa ${conv.session_id.slice(0, 8)}`
}

function formatarDataConversa(conv: ConversaResumo) {
  const raw = conv.updated_at || conv.created_at || conv.updatedAt || conv.createdAt || conv.data
  if (!raw) return 'Sem data'
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return raw
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
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
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedMessageIndex, setCopiedMessageIndex] = useState<number | null>(null)
  const [copiedChatLink, setCopiedChatLink] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [pesquisarWeb, setPesquisarWeb] = useState(false)
  const [googleToken, setGoogleToken] = useState('')
  const [profile, setProfile] = useState<GoogleProfile | null>(null)
  const [conversas, setConversas] = useState<ConversaResumo[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)

  const chatUrl = (id: string) => `/c/${encodeURIComponent(id)}`

  const chatIdFromUrl = () => {
    if (typeof window === 'undefined') return ''
    const match = window.location.pathname.match(/^\/c\/([^\/#?]+)/)
    if (match) return decodeURIComponent(match[1])
    return new URLSearchParams(window.location.search).get('chat') || ''
  }

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
    const initialChatId = chatIdFromUrl()
    if (savedToken) {
      setGoogleToken(savedToken)
      setProfile(decodeJwtProfile(savedToken))
      carregarConversas(savedToken)
      if (initialChatId) carregarHistorico(initialChatId, savedToken, false)
    }
  }, [])


  // Sincroniza a URL com a conversa ativa
  useEffect(() => {
    if (!sessionId || typeof window === 'undefined') return
    const nextUrl = chatUrl(sessionId)
    if (window.location.pathname !== nextUrl) router.replace(nextUrl)
  }, [sessionId, router])

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
    router.push('/')
  }

  const carregarHistorico = async (id: string, token = googleToken, atualizarUrl = true) => {
    if (!token) return

    try {
      setLoading(true)
      const response = await fetch(`${apiUrl}/historico/${id}`, {
        headers: authHeaders(token),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data?.detail || `Erro HTTP ${response.status}`)

      setSessionId(id)
      if (atualizarUrl) router.push(chatUrl(id))
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
        router.push('/')
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
          content: data.resposta || 'A API respondeu sem conteúdo.',
          fontes: data.fontes || [],
        },
      ])

      await carregarConversas()
 } catch (error) {
 const message = error instanceof Error ? error.message : "Erro desconhecido"
 const normalized = message.toLowerCase()
 const authExpired = normalized.includes("token google") || normalized.includes("login google") || normalized.includes("token ausente") || normalized.includes("401")
 if (authExpired) {
 setGoogleToken("")
 setProfile(null)
 setConversas([])
 if (typeof window !== "undefined") {
 window.localStorage.removeItem("helpus_google_token")
 }
 setInput(texto)
 setMessages(prev => [
 ...prev,
 { role: "assistant", content: ["Sua sessão expirou ou perdeu validade.", "", "Entre novamente com o Google para continuar. Mantive sua pergunta na caixa de texto para você reenviar depois do login."].join("\n") },
 ])
 return
 }
 setMessages(prev => [
 ...prev,
 { role: "assistant", content: ["Erro ao conectar com o servidor.", "", "Tente novamente em alguns instantes. Se o problema continuar, verifique a conexão ou o status do serviço.", "", "Detalhe técnico: " + message].join("\n") },
 ])
    } finally {
      setLoading(false)
    }
  }

  async function copiarMensagem(content: string, index: number) {
    if (!navigator.clipboard) return

    await navigator.clipboard.writeText(content)
    setCopiedMessageIndex(index)
    window.setTimeout(() => {
      setCopiedMessageIndex(current => (current === index ? null : current))
    }, 1800)
  }

  async function copiarLinkConversa() {
    if (!sessionId || !navigator.clipboard) return
    const link = `${window.location.origin}${chatUrl(sessionId)}`
    await navigator.clipboard.writeText(link)
    setCopiedChatLink(true)
    window.setTimeout(() => setCopiedChatLink(false), 1800)
  }

  const limparChat = () => {
    setMessages([])
    setSessionId('')
    router.push('/')
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
    <main className="helpus-dark-shell min-h-screen bg-[#212121] text-zinc-100">
      <Script src="https://accounts.google.com/gsi/client" async defer onLoad={inicializarGoogle} />

      <div className="flex min-h-screen w-full flex-col">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-[#212121]/95 px-3 py-2 backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h1 className="text-base font-semibold tracking-tight text-zinc-100">HelpUS</h1>
                <p className="text-xs text-zinc-400">Seu HelpUS Inteligente</p>
              </div>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-zinc-200 transition hover:bg-white/10 lg:hidden"
              >
                Historico
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 text-xs">
              <label className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-zinc-200">
                <input
                  type="checkbox"
                  checked={pesquisarWeb}
                  onChange={(e) => setPesquisarWeb(e.target.checked)}
                  className="h-4 w-4 rounded"
                />
                Pesquisar na web
              </label>

              {profile ? (
                <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2">
                  {profile.picture && (
                    <img src={profile.picture} alt={profile.name} className="h-6 w-6 rounded-full" />
                  )}
                  <span className="max-w-[160px] truncate text-zinc-200">{profile.name}</span>
                  <button onClick={sair} className="font-semibold text-slate-500 hover:text-red-600">
                    Sair
                  </button>
                </div>
              ) : (
                <div id="google-login-button" />
              )}

              <Link
                href="/admin"
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-zinc-200 transition hover:bg-white/10 hover:text-white"
              >
                Admin
              </Link>

              <button
                onClick={limparChat}
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-zinc-200 transition hover:bg-white/10 hover:text-white"
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
                      {tituloConversa(conv)}
                    </div>
                    <div className="mt-1 text-xs text-zinc-400">
                      <span>{formatarDataConversa(conv)}</span>
                                            <span className="mx-1">·</span>
                                            <span>{conv.total_mensagens} mensagens</span>
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
                <div className="mx-auto mt-16 max-w-2xl rounded-2xl border border-white/10 bg-[#2f2f2f] p-8 text-center shadow-2xl shadow-black/20">
                  <p className="text-3xl font-bold text-zinc-100">Como posso ajudar?</p>
                  <p className="mt-3 text-zinc-400">
                    Entre com Google e pergunte algo ao HelpUS.
                  </p>
                  {!profile && (
                    <p className="mt-4 rounded-lg bg-zinc-900 p-3 text-sm text-zinc-300">
                      Entre com Google para iniciar uma conversa segura com o HelpUS.
                    </p>
                  )}
                  <div className="mt-8 grid gap-3 text-left text-sm text-zinc-300 sm:grid-cols-2">
                    <button
                      onClick={() => setInput('Quem é você?')}
                      className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left text-zinc-200 shadow-sm transition hover:-translate-y-0.5 hover:bg-white/10 hover:shadow-md"
                    >
                      Quem é você?
                    </button>
                    <button
                      onClick={() => setInput('Explique em poucas palavras como o HelpUS funciona.')}
                      className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left text-zinc-200 shadow-sm transition hover:-translate-y-0.5 hover:bg-white/10 hover:shadow-md"
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
                          : msg.content.startsWith('Erro ')
                            ? 'border border-rose-200 bg-rose-50 text-rose-950'
                            : 'border border-white/10 bg-[#2f2f2f] text-zinc-100'
                      }`}
                    >
                      <div className={`mb-1 text-sm font-bold ${msg.role === 'user' ? 'text-blue-50' : 'text-zinc-100'}`}>
                        {msg.role === 'user' ? 'Voce' : 'HelpUS'}
                      </div>

                      <section>{renderMessageContent(msg.content)}</section>

                      {msg.role === 'assistant' && (
                        <button
                          type="button"
                          onClick={() => copiarMensagem(msg.content, index)}
                          className="mt-3 rounded-lg border border-white/10 px-3 py-1 text-xs font-medium text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100"
                        >
                          {copiedMessageIndex === index ? 'Copiado' : 'Copiar'}
                        </button>
                      )}

                      {msg.fontes && msg.fontes.length > 0 && (
                        <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3">
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
                                className="block truncate text-sm text-zinc-300 hover:text-white hover:underline"
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
                    <div className="rounded-2xl border border-white/10 bg-[#2f2f2f] px-4 py-3 shadow-sm shadow-black/20">
                      <div className="flex items-center gap-3 text-xs text-zinc-400">
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

            <footer className="border-t border-white/10 bg-[#212121]/95 px-3 pb-4 pt-2 backdrop-blur">
              <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-3xl border border-white/10 bg-[#2f2f2f] p-2 shadow-2xl shadow-black/30 focus-within:border-white/20">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={profile ? 'Pergunte alguma coisa ao HelpUS' : 'Entre com Google para usar o HelpUS'}
                  className="min-h-[44px] flex-1 resize-none rounded-xl border-0 bg-transparent p-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
                  rows={1}
                  disabled={loading || !profile}
                />
                <button
                  onClick={enviarMensagem}
                  disabled={loading || !input.trim() || !profile}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100 text-sm font-bold text-zinc-950 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-30"
                >
                  {loading ? '...' : '↑'}
                </button>
              </div>

              {sessionId && (
                <div className="mx-auto mt-2 flex max-w-3xl items-center justify-center gap-2 text-xs text-zinc-500">
                  <span>Histórico ativo · /c/{sessionId}</span>
                  <button
                    type="button"
                    onClick={copiarLinkConversa}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-medium text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100"
                  >
                    {copiedChatLink ? 'Link copiado' : 'Copiar link'}
                  </button>
                </div>
              )}
            </footer>
          </section>
        </div>
      </div>
    </main>
  )
}
