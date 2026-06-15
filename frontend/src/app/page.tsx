'use client'
import { useRouter } from 'next/navigation'
import Script from 'next/script'
import { useEffect, useRef, useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  fontes?: { titulo: string; url: string; fonte: string }[]
  provider_used?: string
  fallback_reason?: string | null
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
  project_id?: string
}

declare global {
  interface Window {
    google?: any
  }
}

function renderInlineMarkdown(text: string) {
  return text.split(/(`[^`]+`)/g).map((part, index) =>
    part.startsWith('`') && part.endsWith('`')
      ? <code key={index} className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[13px] text-zinc-100">{part.slice(1, -1)}</code>
      : <span key={index}>{part}</span>
  )
}

const HELPUSAI_VISUAL_VERSION = 'v0.31.0-dev'

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
        <pre key={blocks.length} className="overflow-x-auto rounded-2xl border border-white/10 bg-zinc-950 p-4 font-mono text-sm text-zinc-100 shadow-inner shadow-black/30">
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
        <ul key={blocks.length} className="list-disc space-y-1.5 pl-6 marker:text-zinc-500">
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

  return <div className="space-y-4 text-[15px] leading-7 text-inherit sm:text-base">{blocks}</div>
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


interface ProjectMemory {
 id: number
 project_id: string
 title: string
 content: string
 tags?: string
 enabled: boolean
 created_by?: string
 created_at?: string
 updated_at?: string
}

export default function Home() {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const [loading, setLoading] = useState(false)
  const [copiedMessageIndex, setCopiedMessageIndex] = useState<number | null>(null)
  const [copiedChatLink, setCopiedChatLink] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [pesquisarWeb, setPesquisarWeb] = useState(false)
  const [googleToken, setGoogleToken] = useState('')
  const [profile, setProfile] = useState<GoogleProfile | null>(null)
  const [conversas, setConversas] = useState<ConversaResumo[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [actionsMenuOpen, setActionsMenuOpen] = useState(false)
  const [accountMenuOpen, setAccountMenuOpen] = useState(false)
  const [accountPanel, setAccountPanel] = useState<'personalizacao' | 'configuracoes' | 'ajuda' | null>(null)
  const [chatSearch, setChatSearch] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [sidebarNotice, setSidebarNotice] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState('')
  const [sidebarPanel, setSidebarPanel] = useState<'projects' | 'library' | 'memories' | null>(null)
  const [activeProjectId, setActiveProjectId] = useState('general')
  const [projectMemories, setProjectMemories] = useState<ProjectMemory[]>([])
  const [memoryLoading, setMemoryLoading] = useState(false)
  const [memoryNotice, setMemoryNotice] = useState('')
  const [memoryFormOpen, setMemoryFormOpen] = useState(false)
  const [memoryForm, setMemoryForm] = useState({ title: '', content: '', tags: '' })

  const chatUrl = (id: string) => `/c/${encodeURIComponent(id)}`

  const chatIdFromUrl = () => {
    if (typeof window === 'undefined') return ''
    const match = window.location.pathname.match(/^\/c\/([^\/#?]+)/)
    if (match) return decodeURIComponent(match[1])
    return new URLSearchParams(window.location.search).get('chat') || ''
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''
  const providerBadgeDebugEnabled = typeof window !== 'undefined' && window.localStorage.getItem('helpus_provider_debug') === '1'

  const projectLabels: Record<string, string> = {
    general: 'Projeto Geral',
    helpusai: 'WS EUA HelpUSAI Status',
    ai_bridge: 'WS EUA AI Bridge',
    watcher: 'WS EUA Watcher Ativo',
  }
  const activeProjectLabel = projectLabels[activeProjectId] || 'Projeto Geral'
  const projectFilteredConversas = activeProjectId === 'general'
    ? conversas
    : conversas.filter((conv) => (conv.project_id || 'general') === activeProjectId)

  const chatSearchTerm = chatSearch.trim().toLowerCase()
  const conversasFiltradas = chatSearchTerm
    ? projectFilteredConversas.filter((conv) => {
        const titulo = tituloConversa(conv).toLowerCase()
        const data = formatarDataConversa(conv).toLowerCase()
        return titulo.includes(chatSearchTerm) || data.includes(chatSearchTerm)
      })
    : projectFilteredConversas

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
      setSidebarNotice('')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setSidebarNotice(`Nao foi possivel carregar o historico: ${message}`)
    } finally {
      setHistoryLoading(false)
    }
  }

  const carregarMemorias = async (projectId = activeProjectId, token = googleToken) => {
    if (!token) return

    try {
      setMemoryLoading(true)
      const response = await fetch(`${apiUrl}/memorias?project_id=${encodeURIComponent(projectId)}&include_disabled=true`, {
        headers: authHeaders(token),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data?.detail || `Erro HTTP ${response.status}`)
      setProjectMemories(data.memorias || [])
      setMemoryNotice('')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setMemoryNotice(`Nao foi possivel carregar memorias: ${message}`)
    } finally {
      setMemoryLoading(false)
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

  useEffect(() => {
    if (googleToken) {
      carregarMemorias(activeProjectId, googleToken)
    }
  }, [activeProjectId, googleToken])


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
    setActionsMenuOpen(false)
    setAccountMenuOpen(false)
    setAccountPanel(null)
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
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  const apagarConversa = async (id: string) => {
    if (!googleToken) return

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
      setDeleteConfirmId('')
      setSidebarNotice('Conversa apagada.')
      setTimeout(() => setSidebarNotice(''), 3000)
      setSidebarOpen(false)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setSidebarNotice(`Nao foi possivel apagar a conversa: ${message}`)
    }
  }

  const enviarMensagem = async () => {
    const texto = input.trim()
    if (!texto || loading) return

    if (!googleToken) {
      setTimeout(() => inputRef.current?.focus(), 0)
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Entre com sua conta Google para usar o HelpUS.' },
      ])
      return
    }

    setMessages(prev => [...prev, { role: 'user', content: texto }])
    setInput('')
    setTimeout(() => inputRef.current?.focus(), 0)
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
          project_id: activeProjectId,
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
          provider_used: data.provider_used || '',
          fallback_reason: data.fallback_reason || null,
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
  { role: 'assistant', content: ['Sua sessao expirou ou perdeu validade.', '', 'Entre novamente com o Google para continuar. Mantive sua pergunta na caixa de texto para voce reenviar depois do login.'].join(String.fromCharCode(10)) },
 ])
 return
 }
 setMessages(prev => [
 ...prev,
  { role: 'assistant', content: ['Erro ao conectar com o servidor.', '', 'Tente novamente em alguns instantes. Se o problema continuar, verifique a conexao ou o status do servico.', '', 'Detalhe tecnico: ' + message].join(String.fromCharCode(10)) },
 ])
    } finally {
      setLoading(false)
    }
  }

  async function copiarMensagem(content: string, index: number) {
    if (!navigator.clipboard) {
      console.warn('Clipboard indisponivel para copiar mensagem')
      return
    }

    await navigator.clipboard.writeText(content)
    setCopiedMessageIndex(index)
    window.setTimeout(() => {
      setCopiedMessageIndex(current => (current === index ? null : current))
    }, 1800)
  }

  async function copiarLinkConversa() {
    if (!sessionId) return
    if (!navigator.clipboard) {
      console.warn('Clipboard indisponivel para copiar link')
      return
    }
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
    <main className="helpus-dark-shell h-screen overflow-hidden bg-[#212121] text-zinc-100">
      <Script src="https://accounts.google.com/gsi/client" async defer onLoad={inicializarGoogle} />

      <div className="flex h-full w-full flex-col overflow-hidden">
        <header className="z-40 flex-none border-b border-white/10 bg-[#212121]/95 px-3 py-2 backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-zinc-200 transition hover:bg-white/10"
                aria-label="Abrir ou recolher menu"
              >
                Menu
              </button>
              <div>
                <h1 className="text-base font-semibold tracking-tight text-zinc-100">Projeto Geral</h1>
                <div className="flex items-center gap-2">
                  <p className="text-xs text-zinc-400">HelpUS!AI</p>
                  <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-zinc-500" title="Versao visual temporaria da HelpUSAI">{HELPUSAI_VISUAL_VERSION}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-200 sm:flex">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Sistema operacional
              </span>
              <div className="relative">
                <button
                  onClick={() => setActionsMenuOpen(!actionsMenuOpen)}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-zinc-200 transition hover:bg-white/10 hover:text-white"
                  aria-haspopup="menu"
                  aria-expanded={actionsMenuOpen}
                  title="Opcoes"
                >
                  ...
                </button>
                <div className={actionsMenuOpen ? "absolute right-0 top-10 z-50 w-64 overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/95 p-2 text-sm text-zinc-100 shadow-2xl shadow-black/40 backdrop-blur" : "hidden"} role="menu">
                  <button onClick={() => { setActionsMenuOpen(false); limparChat() }} className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10" role="menuitem">
                    <span>Nova conversa</span>
                    <span className="text-zinc-500">+</span>
                  </button>
                  <button onClick={() => { setActionsMenuOpen(false); setSidebarPanel('projects'); setSidebarOpen(true) }} className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10" role="menuitem">
                    <span>Projetos</span>
                    <span className="rounded-full bg-emerald-400/10 px-2 py-0.5 text-[11px] text-emerald-200">ativo</span>
                  </button>
                  <button onClick={() => { setActionsMenuOpen(false); router.push('/admin') }} className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10" role="menuitem">
                    <span>Painel operacional</span>
                    <span className="rounded-full bg-white/5 px-2 py-0.5 text-[11px] text-zinc-300">/admin</span>
                  </button>
                  <div className="my-2 h-px bg-white/10" />
                  {profile ? (
                    <button onClick={sair} className="block w-full rounded-xl px-3 py-2.5 text-left text-rose-200 transition hover:bg-rose-500/10" role="menuitem">Sair da conta Google</button>
                  ) : (
                    <button
                      onClick={() => {
                        setActionsMenuOpen(false)
                        window.google?.accounts?.id?.prompt()
                      }}
                      className="block w-full rounded-xl px-3 py-2.5 text-left text-zinc-100 transition hover:bg-white/10"
                      role="menuitem"
                    >
                      Entrar com Google
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div id="google-login-button" className="hidden" />
        </header>

        <div className="flex min-h-0 flex-1 overflow-hidden">
          <aside
            className={`${sidebarOpen ? 'fixed inset-y-0 left-0 z-50 block w-80 max-w[85vw]' : 'hidden'} border-r border-white/10 bg[-#171717] p-2 text-zinc-100 shadow-2xl shadow-black/40 backdrop-blur lg:static lg:z-auto lg:block lg:w-72 lg:max-w-none lg:flex-none`}
          >
            <div className="flex h-full flex-col">
              <div className="mb-2 flex items-center justify-between px-2 py-2">
                <button
                  onClick={limparChat}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-zinc-100 transition hover:bg-white/10"
                >
                  <span className="text-base">+</span>
                  Nova conversa
                </button>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="rounded-xl px-3 py-2 text-sm text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100 lg:hidden"
                  aria-label="Fechar menu"
                >
                  x
                </button>
              </div>

              <nav className="space-y-1 px-2 text-sm">
                <button
                  onClick={limparChat}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-zinc-100 transition hover:bg-white/10"
                >
                  <span className="w-5 text-center">+</span>
                  <span>Nova conversa</span>
                </button>
                <label className="flex w-full items-center gap-3 rounded-xl bg-white/5 px-3 py-2.5 text-left text-zinc-300 ring-1 ring-white/10 transition focus-within:ring-white/20">
                  <span className="w-5 text-center text-zinc-500">?</span>
                  <input
                    value={chatSearch}
                    onChange={(event) => setChatSearch(event.target.value)}
                    placeholder="Buscar chats"
                    className="min-w-0 flex-1 bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 outline-none"
                  />
                </label>
                <button
                  onClick={() => setSidebarPanel(sidebarPanel === 'library' ? null : 'library')}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10 ${sidebarPanel === 'library' ? 'bg-white/10 text-zinc-100' : 'text-zinc-300'}`}
                >
                  <span className="w-5 text-center">[]</span>
                  <span>Memórias</span>
                </button>
              </nav>

              {sidebarPanel && (
                <div className="mx-2 mt-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-zinc-300">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <div className="font-medium text-zinc-100">
                      {sidebarPanel === 'projects' ? 'Projetos' : 'Memórias'}
                    </div>
                    <button onClick={() => setSidebarPanel(null)} className="rounded-lg px-2 py-1 text-xs text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100">
                      Fechar
                    </button>
                  </div>
                  {sidebarPanel === 'projects' ? (
                    <div className="space-y-2 text-xs leading-5 text-zinc-400">
                      <p>Use os atalhos abaixo para filtrar conversas por frente de trabalho.</p>
                      <div className="flex flex-wrap gap-2">
                        <button onClick={() => { setChatSearch(''); setActiveProjectId('helpusai') }} className="rounded-full bg-white/10 px-3 py-1 text-zinc-200">HelpUSAI</button>
                        <button onClick={() => { setChatSearch(''); setActiveProjectId('ai_bridge') }} className="rounded-full bg-white/10 px-3 py-1 text-zinc-200">AI Bridge</button>
                        <button onClick={() => { setChatSearch(''); setActiveProjectId('watcher') }} className="rounded-full bg-white/10 px-3 py-1 text-zinc-200">Watcher</button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2 text-xs leading-5 text-zinc-400">
                      <p>Use esta area para guardar memorias ativas do projeto: regras, decisoes, comandos, IDs e aprendizados.</p>
                      <p>As memorias entram como contexto adicional da HelpUS AI quando o projeto estiver ativo.</p>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-4 px-2">
                <div className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                  Projetos
                </div>
                <div className="space-y-1 text-sm">
                  <button
                    onClick={() => setSidebarPanel(sidebarPanel === 'projects' ? null : 'projects')}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left transition hover:bg-white/10 ${sidebarPanel === 'projects' ? 'bg-white/10 text-zinc-100' : 'text-zinc-300'}`}
                  >
                    <span className="w-5 text-center">+</span>
                    <span>Novo projeto</span>
                    <span className="ml-auto rounded-full bg-white/5 px-2 py-0.5 text-[11px] text-zinc-400">painel</span>
                  </button>
                  <button onClick={() => setChatSearch('')} className="w-full rounded-xl bg-white/10 px-3 py-2 text-left text-zinc-100 transition hover:bg-white/15" title="Mostrar todos os chats">
                    <div className="flex items-center gap-3">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      <span className="truncate">Projeto Geral</span>
                    </div>
                  </button>
                  <button onClick={() => { setChatSearch(''); setActiveProjectId('helpusai') }} className="w-full rounded-xl px-3 py-2 text-left text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100" title="Filtrar chats deste projeto">
                    <div className="truncate">WS EUA HelpUSAI Status</div>
                  </button>
                  <button onClick={() => { setChatSearch(''); setActiveProjectId('ai_bridge') }} className="w-full rounded-xl px-3 py-2 text-left text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100" title="Filtrar chats deste projeto">
                    <div className="truncate">WS EUA AI Bridge</div>
                  </button>
                  <button onClick={() => { setChatSearch(''); setActiveProjectId('watcher') }} className="w-full rounded-xl px-3 py-2 text-left text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100" title="Filtrar chats deste projeto">
                    <div className="truncate">WS EUA Watcher Ativo</div>
                  </button>
                </div>
              </div>

              <div className="mt-4 flex-1 overflow-y-auto px-2 pr-1">
                <div className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                  Chats recentes - {activeProjectLabel}
                </div>

                {sidebarNotice && (
                  <p className="mb-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs leading-5 text-zinc-300">
                    {sidebarNotice}
                  </p>
                )}

                {!profile && (
                  <p className="rounded-xl bg-white/5 px-3 py-3 text-sm text-zinc-400">
                    Entre com Google para ver seu historico.
                  </p>
                )}

                {profile && conversas.length === 0 && (
                  <p className="rounded-xl bg-white/5 px-3 py-3 text-sm text-zinc-400">
                    Nenhuma conversa salva ainda.
                  </p>
                )}

                {profile && conversas.length > 0 && conversasFiltradas.length === 0 && (
                  <p className="rounded-xl bg-white/5 px-3 py-3 text-sm text-zinc-400">
                    Nenhum chat encontrado.
                  </p>
                )}

                <div className="space-y-1">
                  {conversasFiltradas.map((conv) => (
                    <div
                      key={conv.session_id}
                      className={`rounded-xl transition hover:bg-white/10 ${sessionId === conv.session_id ? 'bg-white/10 text-zinc-100' : 'text-zinc-300'}`}
                    >
                      <div className="flex items-start gap-2 px-3 py-2.5">
                        <button
                          onClick={() => carregarHistorico(conv.session_id)}
                          className="min-w-0 flex-1 text-left text-sm"
                        >
                          <div className="truncate font-medium">{tituloConversa(conv)}</div>
                          <div className="mt-0.5 truncate text-xs text-zinc-500">
                            {formatarDataConversa(conv)} - {conv.total_mensagens} mensagens
                          </div>
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(deleteConfirmId === conv.session_id ? '' : conv.session_id)}
                          className="rounded-lg px-2 py-1 text-xs text-zinc-500 transition hover:bg-white/10 hover:text-rose-200"
                          title="Apagar conversa"
                        >
                          x
                        </button>
                      </div>
                      {deleteConfirmId === conv.session_id && (
                        <div className="mx-3 mb-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-2 text-xs text-rose-100">
                          <div className="mb-2">Apagar esta conversa?</div>
                          <div className="flex gap-2">
                            <button onClick={() => apagarConversa(conv.session_id)} className="rounded-lg bg-rose-500/20 px-2 py-1 text-rose-100 transition hover:bg-rose-500/30">Apagar</button>
                            <button onClick={() => setDeleteConfirmId('')} className="rounded-lg px-2 py-1 text-zinc-300 transition hover:bg-white/10">Cancelar</button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative mt-3 border-t border-white/10 px-2 pt-3">
                <button
                  onClick={() => setAccountMenuOpen(!accountMenuOpen)}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10"
                >
                  {profile?.picture ? (
                    <img src={profile.picture} alt="" className="h-8 w-8 rounded-full" />
                  ) : (
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/20 text-sm font-semibold text-emerald-200">
                      H
                    </span>
                  )}
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-zinc-100">{profile?.name || 'HelpUS'}</span>
                    <span className="block truncate text-xs text-zinc-500">{profile?.email || 'Entrar com Google'}</span>
                  </span>
                  <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[11px] font-medium text-violet-200">Plus</span>
                </button>

                <div className={accountMenuOpen ? "absolute bottom-16 left-2 right-2 z-50 overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/95 p-2 text-sm text-zinc-100 shadow-2xl shadow-black/50 backdrop-blur" : "hidden"}>
                  <div className="flex items-center gap-3 px-3 py-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-sm font-semibold text-emerald-200">
                      H
                    </span>
                    <div className="min-w-0">
                      <div className="truncate font-medium">{profile?.name || 'HelpUS'}</div>
                      <div className="truncate text-xs text-zinc-500">{profile?.email || 'Conta Google'}</div>
                    </div>
                  </div>
                  <div className="my-1 h-px bg-white/10" />
                  <button onClick={() => setAccountPanel('personalizacao')} className={`block w-full rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10 ${accountPanel === 'personalizacao' ? 'bg-white/10 text-white' : ''}`}>Personalizacao</button>
                  <button onClick={() => setAccountPanel('configuracoes')} className={`block w-full rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10 ${accountPanel === 'configuracoes' ? 'bg-white/10 text-white' : ''}`}>Configuracoes</button>
                  <button onClick={() => setAccountPanel('ajuda')} className={`block w-full rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10 ${accountPanel === 'ajuda' ? 'bg-white/10 text-white' : ''}`}>Ajuda</button>
                  {accountPanel && (
                    <div className="mt-2 space-y-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2.5 text-xs leading-5 text-zinc-400">
                      {accountPanel === 'personalizacao' && (
                        <div className="space-y-1">
                          <div className="font-medium text-zinc-200">Personalizacao</div>
                          <p>Tema escuro ativo, atalhos de projetos no menu lateral e busca de chats integrada.</p>
                          <p>Modelo e preferencias avancadas serao conectados ao perfil quando a API de configuracoes estiver disponivel.</p>
                        </div>
                      )}
                      {accountPanel === 'configuracoes' && (
                        <div className="space-y-1">
                          <div className="font-medium text-zinc-200">Configuracoes</div>
                          <p>Conta Google conectada: {profile?.email || 'nao conectado'}.</p>
                          <p>Historico, projetos e biblioteca usam a mesma sessao autenticada.</p>
                          <p>Privacidade: conversas ficam associadas ao email autenticado.</p>
                        </div>
                      )}
                      {accountPanel === 'ajuda' && (
                        <div className="space-y-1">
                          <div className="font-medium text-zinc-200">Ajuda</div>
                          <p>Use Nova conversa para iniciar um atendimento limpo.</p>
                          <p>Use Projetos para filtrar frentes de trabalho e Memórias para guardar regras, decisoes e aprendizados.</p>
                          <p>Se a sessao expirar, entre novamente com Google e reenvie a pergunta preservada na caixa.</p>
                        </div>
                      )}
                    </div>
                  )}
                  <div className="my-1 h-px bg-white/10" />
                  {profile ? (
                    <button onClick={sair} className="block w-full rounded-xl px-3 py-2.5 text-left text-rose-200 transition hover:bg-rose-500/10">Sair</button>
                  ) : (
                    <button
                      onClick={() => {
                        setAccountMenuOpen(false)
                        setAccountPanel(null)
                        window.google?.accounts?.id?.prompt()
                      }}
                      className="block w-full rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10"
                    >
                      Entrar com Google
                    </button>
                  )}
                </div>
              </div>
            </div>
          </aside>

          <section className="flex min-h-0 min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6">
              {messages.length === 0 && (
                <div className="min-h-[28vh]" aria-hidden="true" />
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
                      {providerBadgeDebugEnabled && msg.provider_used && (
                        <div className="mt-3 rounded-lg border border-white/5 bg-white/[0.02] px-2 py-1 text-[11px] text-zinc-500">
                          Provider: {msg.provider_used}{msg.fallback_reason ? ` (${msg.fallback_reason})` : ''}
                        </div>
                      )}

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
                        HelpUS esta pensando...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <footer className="border-t border-white/10 bg-[#212121]/95 px-3 pb-4 pt-3 backdrop-blur">
              <div className="mx-auto max-w-4xl">
                <div className="flex items-end gap-2 rounded-[2rem] border border-white/10 bg-[#2f2f2f] p-2 shadow-2xl shadow-black/30 focus-within:border-white/20">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={profile ? 'Envie uma mensagem ao HelpUS' : 'Entre com Google para usar o HelpUS'}
                    className="max-h-32 min-h-[52px] flex-1 resize-none rounded-2xl border-0 bg-transparent px-3 py-3.5 text-sm leading-6 text-zinc-100 outline-none placeholder:text-zinc-500"
                    rows={1}
                    disabled={loading || !profile}
                  />
                  <button
                    onClick={enviarMensagem}
                    disabled={loading || !input.trim() || !profile}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100 text-sm font-bold text-zinc-950 transition hover:scale-105 hover:bg-white disabled:cursor-not-allowed disabled:opacity-30"
                    aria-label="Enviar mensagem"
                  >
                    {loading ? '...' : '->'}
                  </button>
                </div>

                <p className="mt-2 text-center text-xs text-zinc-500">
                  O HelpUS pode consultar fontes e a web automaticamente quando necessario.
                </p>

                {sessionId && (
                  <div className="mx-auto mt-2 flex max-w-4xl items-center justify-center gap-2 text-xs text-zinc-500">
                    <span>Historico ativo - /c/{sessionId}</span>
                    <button
                      type="button"
                      onClick={copiarLinkConversa}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-medium text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100"
                    >
                      {copiedChatLink ? 'Link copiado' : 'Copiar link'}
                    </button>
                  </div>
                )}
              </div>
            </footer>
          </section>
        </div>
      </div>
    </main>
  )
}
