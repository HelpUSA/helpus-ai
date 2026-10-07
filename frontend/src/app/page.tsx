'use client'

import Image from 'next/image'
import { useRouter } from 'next/navigation'
import Script from 'next/script'
import { useEffect, useRef, useState } from 'react'
import {
  MarkdownMessage,
  SafeSourceLink,
  type MessageSource,
} from './markdown-message'

type AgentTraceItem = {
  label: string
  status: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  image_url?: string
  fontes?: MessageSource[]
  provider_used?: string
  agent_trace?: AgentTraceItem[]
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
  total_mensagens: number
  project_id?: string
}

declare global {
  interface Window {
    google?: any
    webkitSpeechRecognition?: any
    SpeechRecognition?: any
  }
}


const MODEL_OPTIONS = [
  { id: 'gemini-2.5-flash-lite', name: 'Flash-Lite', desc: 'Rápido e eficiente' },
  { id: 'gemini-2.5-flash', name: 'Flash', desc: 'Equilíbrio ideal de inteligência' },
  { id: 'gemini-2.5-pro', name: 'Pro', desc: 'Raciocínio profundo e análise' },
]

function decodeJwtProfile(token: string): GoogleProfile | null {
  try {
    const payload = token.split('.')[1]
    const json = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return {
      email: json.email || '',
      name: json.name || json.email || 'Usuário',
      picture: json.picture || '',
    }
  } catch {
    return null
  }
}

export default function HelpUSGeminiApp() {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [conversas, setConversas] = useState<ConversaResumo[]>([])
  const [googleToken, setGoogleToken] = useState('')
  const [profile, setProfile] = useState<GoogleProfile | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeModel, setActiveModel] = useState(MODEL_OPTIONS[0])
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'spark'>('chat')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [accountMenuOpen, setAccountMenuOpen] = useState(false)
  const [aboutModalOpen, setAboutModalOpen] = useState(false)
  const [webSearchEnabled, setWebSearchEnabled] = useState(false)

  // Upload de imagem multimodal
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [selectedImageBase64, setSelectedImageBase64] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Chamada de voz em tempo real
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState<'idle' | 'listening' | 'speaking'>('idle')
  const [voiceTranscript, setVoiceTranscript] = useState('')
  const voiceRecognitionRef = useRef<any>(null)

  // Controle de scroll e viewport
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''
  const googleClientId =
    process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
    '812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com'

  // Carrega token salvo e conversas
  useEffect(() => {
    const savedToken = window.localStorage.getItem('helpus_google_token') || ''
    if (savedToken) {
      setGoogleToken(savedToken)
      setProfile(decodeJwtProfile(savedToken))
      carregarConversas(savedToken)
    }
  }, [])

  // Auto-scroll
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  // Inicializa Google GIS
  const inicializarGoogle = () => {
    if (typeof window === 'undefined' || !window.google?.accounts?.id || !googleClientId) return

    try {
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
        auto_select: false,
        cancel_on_tap_outside: true,
      })

      // Renderiza botão oficial discreto no container escondido para servir de acionador nativo
      const container = document.getElementById('google-native-signin-anchor')
      if (container) {
        container.innerHTML = ''
        window.google.accounts.id.renderButton(container, {
          theme: 'filled_blue',
          size: 'large',
          text: 'signin',
          shape: 'pill',
          locale: 'pt-BR',
        })
      }
    } catch (e) {
      console.warn('[HelpUS Auth] Falha na inicialização do Google GIS:', e)
    }
  }

  // Disparo do login estilo Gemini (sem estampar dados do usuário no botão antes)
  const dispararLoginGoogle = () => {
    if (typeof window === 'undefined') return
    const btn = document.querySelector('#google-native-signin-anchor div[role="button"]') as HTMLElement
    if (btn) {
      btn.click()
      return
    }
    if (window.google?.accounts?.id) {
      inicializarGoogle()
      window.google.accounts.id.prompt()
    }
  }

  // Logout
  const sair = () => {
    setGoogleToken('')
    setProfile(null)
    setConversas([])
    setMessages([])
    setSessionId('')
    setAccountMenuOpen(false)
    setSettingsOpen(false)
    window.localStorage.removeItem('helpus_google_token')
    if (typeof window !== 'undefined' && window.google?.accounts?.id?.disableAutoSelect) {
      window.google.accounts.id.disableAutoSelect()
    }
    router.push('/')
  }

  // Carregar histórico de conversas do usuário
  const carregarConversas = async (token = googleToken) => {
    if (!token) return
    try {
      const res = await fetch(`${apiUrl}/conversas`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setConversas(Array.isArray(data) ? data : data.conversas || [])
      }
    } catch {
      // tolerante a falhas
    }
  }

  // Carregar conversa específica
  const abrirConversa = async (id: string) => {
    if (!googleToken) return
    try {
      setLoading(true)
      setSessionId(id)
      const res = await fetch(`${apiUrl}/historico/${id}`, {
        headers: { Authorization: `Bearer ${googleToken}` },
      })
      if (res.ok) {
        const data = await res.json()
        setMessages(
          (data.mensagens || []).map((m: any) => ({
            role: m.role,
            content: m.content || m.mensagem || '',
            image_url: m.image_url,
            fontes: m.fontes || [],
          }))
        )
      }
    } catch {
      // falha silenciosa
    } finally {
      setLoading(false)
    }
  }

  // Iniciar nova conversa
  const novaConversa = () => {
    setMessages([])
    setSessionId('')
    setInput('')
    setSelectedImage(null)
    setSelectedImageBase64(null)
    inputRef.current?.focus()
  }

  // Excluir conversa
  const excluirConversa = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!googleToken) return
    try {
      await fetch(`${apiUrl}/conversa/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${googleToken}` },
      })
      setConversas((prev) => prev.filter((c) => c.session_id !== id))
      if (sessionId === id) novaConversa()
    } catch {
      // ignore
    }
  }

  // Enviar mensagem para a IA
  const enviarMensagem = async (texto = input) => {
    const textoLimpo = texto.trim()
    if (!textoLimpo && !selectedImageBase64) return
    if (loading) return

    // Se não estiver logado, dispara login oficial estilo Gemini
    if (!googleToken) {
      dispararLoginGoogle()
      return
    }

    const imagemAnexa = selectedImage
    const imagemBase64 = selectedImageBase64

    setInput('')
    setSelectedImage(null)
    setSelectedImageBase64(null)

    const novaMensagemUsuario: Message = {
      role: 'user',
      content: textoLimpo,
      image_url: imagemAnexa || undefined,
    }

    setMessages((prev) => [...prev, novaMensagemUsuario])
    setLoading(true)

    // Mensagem temporária do assistente para streaming
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: '',
        provider_used: activeModel.name,
      },
    ])

    try {
      abortControllerRef.current = new AbortController()

      // Tenta rota SSE /chat/stream
      const resStream = await fetch(`${apiUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${googleToken}`,
        },
        body: JSON.stringify({
          mensagem: textoLimpo,
          session_id: sessionId || undefined,
          pesquisar_web: webSearchEnabled,
          imagem_base64: imagemBase64 || undefined,
          model: activeModel.id,
        }),
        signal: abortControllerRef.current.signal,
      })

      if (resStream.ok && resStream.body) {
        const reader = resStream.body.getReader()
        const decoder = new TextDecoder()
        let respostaAcumulada = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim()
              if (dataStr === '[DONE]') continue
              try {
                const parsed = JSON.parse(dataStr)
                if (parsed.text) {
                  respostaAcumulada += parsed.text
                  setMessages((prev) => {
                    const copia = [...prev]
                    const last = copia[copia.length - 1]
                    if (last && last.role === 'assistant') {
                      copia[copia.length - 1] = {
                        ...last,
                        content: respostaAcumulada,
                        fontes: parsed.fontes || last.fontes,
                      }
                    }
                    return copia
                  })
                }
                if (parsed.session_id && !sessionId) {
                  setSessionId(parsed.session_id)
                }
              } catch {
                respostaAcumulada += dataStr
                setMessages((prev) => {
                  const copia = [...prev]
                  const last = copia[copia.length - 1]
                  if (last && last.role === 'assistant') {
                    copia[copia.length - 1] = { ...last, content: respostaAcumulada }
                  }
                  return copia
                })
              }
            }
          }
        }
        carregarConversas(googleToken)
        return
      }

      // Fallback padrão /chat síncrono
      const res = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${googleToken}`,
        },
        body: JSON.stringify({
          mensagem: textoLimpo,
          session_id: sessionId || undefined,
          pesquisar_web: webSearchEnabled,
          imagem_base64: imagemBase64 || undefined,
          model: activeModel.id,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setMessages((prev) => {
          const copia = [...prev]
          copia[copia.length - 1] = {
            role: 'assistant',
            content: data.resposta || 'Sem resposta gerada.',
            fontes: data.fontes || [],
            provider_used: data.provider_used || activeModel.name,
          }
          return copia
        })
        if (data.session_id && !sessionId) {
          setSessionId(data.session_id)
        }
        carregarConversas(googleToken)
      } else {
        throw new Error(`Erro na API (${res.status})`)
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => {
          const copia = [...prev]
          copia[copia.length - 1] = {
            role: 'assistant',
            content: 'Desculpe, ocorreu uma instabilidade momentânea ao processar sua solicitação.',
          }
          return copia
        })
      }
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }

  // Upload de Imagem
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      const result = event.target?.result as string
      if (result) {
        setSelectedImage(result)
        setSelectedImageBase64(result.split(',')[1] || '')
      }
    }
    reader.readAsDataURL(file)
  }

  // Copiar texto da resposta
  const copiarTexto = (texto: string, idx: number) => {
    navigator.clipboard.writeText(texto)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  // Ouvir resposta (Text-to-Speech)
  const ouvirTexto = (texto: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(texto)
    utterance.lang = 'pt-BR'
    window.speechSynthesis.speak(utterance)
  }

  // Reconhecimento de Voz (Microfone)
  const startVoiceRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return
    const rec = new SpeechRecognition()
    rec.lang = 'pt-BR'
    rec.continuous = false
    rec.interimResults = true
    rec.onstart = () => setVoiceStatus('listening')
    rec.onresult = (event: any) => {
      const current = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join('')
      setVoiceTranscript(current)
    }
    rec.onend = () => {
      setVoiceStatus('idle')
      if (voiceTranscript) {
        setInput(voiceTranscript)
        setIsVoiceModalOpen(false)
      }
    }
    voiceRecognitionRef.current = rec
    rec.start()
  }

  // Filtragem de conversas na busca
  const conversasFiltradas = conversas.filter((c) =>
    (c.titulo || `Conversa ${c.session_id.slice(0, 6)}`)
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
  )

  const firstName = profile?.name ? profile.name.split(' ')[0] : 'Help'

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        async
        defer
        onLoad={inicializarGoogle}
      />

      {/* Anchor invisível para inicialização técnica do botão Google sem poluir a interface */}
      <div id="google-native-signin-anchor" className="hidden" />

      <div className="flex h-screen w-screen overflow-hidden bg-[#131314] text-[#e3e3e3] font-sans">
        {/* ================= BARRA LATERAL (SIDEBAR GEMINI) ================= */}
        <aside
          className={`${
            sidebarOpen ? 'w-72' : 'w-0 -translate-x-full lg:w-16 lg:translate-x-0'
          } flex flex-col border-r border-[#242526] bg-[#1e1f20] transition-all duration-300 ease-in-out z-40 shrink-0 overflow-hidden`}
        >
          {/* Topo da Sidebar */}
          <div className="flex h-16 items-center justify-between px-3.5">
            <div className="flex items-center gap-2.5 min-w-0">
              <button
                onClick={() => setSidebarOpen((prev) => !prev)}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                title={sidebarOpen ? 'Recolher menu' : 'Expandir menu'}
                type="button"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
                </svg>
              </button>

              {sidebarOpen && (
                <div className="flex items-center gap-2 min-w-0 cursor-pointer" onClick={novaConversa}>
                  <div className="relative h-7 w-7 shrink-0 overflow-hidden rounded-full ring-1 ring-white/10">
                    <Image
                      src="/logo-helpus.png"
                      alt="HelpUS Logo"
                      fill
                      className="object-cover"
                      priority
                    />
                  </div>
                  <span className="text-lg font-semibold tracking-tight text-[#e3e3e3]">
                    HelpUS
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Conteúdo da Sidebar quando expandida */}
          {sidebarOpen ? (
            <div className="flex flex-1 flex-col overflow-y-auto px-3 py-2 min-h-0">
              {/* Abas Toggle (Chat | Spark) estilo Gemini Foto 4 */}
              <div className="mb-3 flex rounded-full bg-[#131314] p-1 text-xs font-medium text-[#c4c7c5]">
                <button
                  type="button"
                  onClick={() => setActiveTab('chat')}
                  className={`flex-1 rounded-full py-1.5 transition ${
                    activeTab === 'chat'
                      ? 'bg-[#282a2c] text-white shadow-sm'
                      : 'hover:text-white'
                  }`}
                >
                  Chat
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('spark')}
                  className={`flex-1 rounded-full py-1.5 transition flex items-center justify-center gap-1 ${
                    activeTab === 'spark'
                      ? 'bg-[#282a2c] text-white shadow-sm'
                      : 'hover:text-white'
                  }`}
                >
                  <span>Spark</span>
                  <span className="rounded bg-[#004a77] px-1 py-0.2 text-[9px] font-bold text-[#7fcfff]">
                    BETA
                  </span>
                </button>
              </div>

              {/* Botão Nova Conversa */}
              <button
                type="button"
                onClick={novaConversa}
                className="mb-2 flex w-full items-center gap-3 rounded-full bg-[#131314] px-4 py-3 text-sm font-medium text-[#e3e3e3] hover:bg-[#282a2c] transition shadow-sm"
              >
                <svg className="h-4 w-4 text-[#7fcfff]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Nova conversa</span>
              </button>

              {/* Ações Rápidas (Buscar, Imagens) */}
              <div className="mb-3 space-y-0.5">
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar conversas..."
                    className="w-full rounded-full bg-[#131314] px-9 py-2 text-xs text-[#e3e3e3] placeholder-[#8e918f] outline-none focus:ring-1 focus:ring-[#7fcfff]"
                  />
                  <svg className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#8e918f]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Analisar imagens</span>
                </button>
              </div>

              {/* Se NÃO logado: Card Informativo do Gemini Foto 2 */}
              {!googleToken && (
                <div className="my-2 rounded-2xl border border-white/5 bg-[#131314] p-3.5 text-xs text-[#c4c7c5]">
                  <div className="flex items-start gap-2">
                    <span className="text-[#7fcfff]">ⓘ</span>
                    <div>
                      <span>Faça login para salvar seu histórico de conversas e memórias.</span>
                      <button
                        type="button"
                        onClick={dispararLoginGoogle}
                        className="mt-2 block font-semibold text-[#7fcfff] underline hover:text-[#a8e0ff]"
                      >
                        Fazer login agora
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Se logado: Lista de Recentes estilo Gemini Foto 4 */}
              {googleToken && (
                <div className="flex-1 overflow-y-auto min-h-0 space-y-1 pr-1">
                  <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[#8e918f]">
                    Recentes
                  </div>
                  {conversasFiltradas.length === 0 ? (
                    <div className="px-2 py-3 text-xs text-[#8e918f]">
                      Nenhuma conversa encontrada.
                    </div>
                  ) : (
                    conversasFiltradas.map((conv) => {
                      const ativa = sessionId === conv.session_id
                      const titulo = conv.titulo || `Conversa ${conv.session_id.slice(0, 8)}`
                      return (
                        <div
                          key={conv.session_id}
                          onClick={() => abrirConversa(conv.session_id)}
                          className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs cursor-pointer transition ${
                            ativa
                              ? 'bg-[#004a77] text-white font-medium'
                              : 'text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white'
                          }`}
                        >
                          <span className="truncate pr-2">{titulo}</span>
                          <button
                            type="button"
                            onClick={(e) => excluirConversa(conv.session_id, e)}
                            className="hidden shrink-0 text-[#8e918f] hover:text-rose-400 group-hover:block"
                            title="Excluir"
                          >
                            ×
                          </button>
                        </div>
                      )
                    })
                  )}
                </div>
              )}
            </div>
          ) : (
            // Sidebar colapsada em ícones (modo mini)
            <div className="flex flex-1 flex-col items-center gap-3 py-3">
              <button
                type="button"
                onClick={novaConversa}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-[#131314] text-[#7fcfff] hover:bg-[#282a2c] transition"
                title="Nova conversa"
              >
                +
              </button>
            </div>
          )}

          {/* Rodapé da Sidebar */}
          <div className="border-t border-[#242526] p-2.5">
            {profile ? (
              // Rodapé com usuário logado estilo Gemini Foto 4
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setAccountMenuOpen((prev) => !prev)}
                  className="flex w-full items-center justify-between rounded-2xl p-2 hover:bg-[#282a2c] transition text-left"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {profile.picture ? (
                      <img
                        src={profile.picture}
                        alt={profile.name}
                        className="h-8 w-8 rounded-full object-cover ring-1 ring-white/10"
                      />
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#374151] text-xs font-semibold text-white">
                        {firstName[0]}
                      </div>
                    )}
                    {sidebarOpen && (
                      <div className="min-w-0">
                        <div className="truncate text-xs font-semibold text-[#e3e3e3]">
                          {profile.name}
                        </div>
                        <div className="flex items-center gap-1 text-[10px] text-[#7fcfff]">
                          <span>HelpUS</span>
                          <span className="rounded bg-[#004a77] px-1 py-0.2 font-bold text-[#7fcfff]">
                            Pro
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                  {sidebarOpen && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSettingsOpen((prev) => !prev)
                      }}
                      className="text-[#8e918f] hover:text-white p-1"
                    >
                      ⚙
                    </button>
                  )}
                </button>

                {/* Popover da Conta */}
                {accountMenuOpen && (
                  <div className="absolute bottom-14 left-0 z-50 w-60 rounded-2xl border border-[#2d2e30] bg-[#1e1f20] p-2 shadow-2xl">
                    <div className="px-3 py-2 text-xs border-b border-white/5">
                      <div className="font-semibold text-white truncate">{profile.name}</div>
                      <div className="text-[11px] text-[#8e918f] truncate">{profile.email}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setAccountMenuOpen(false)
                        router.push('/admin')
                      }}
                      className="mt-1 flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                    >
                      <span>Painel Operacional</span>
                      <span className="text-[10px] text-[#8e918f]">/admin</span>
                    </button>
                    <button
                      type="button"
                      onClick={sair}
                      className="mt-1 flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs text-rose-300 hover:bg-rose-500/10 transition"
                    >
                      <span>Sair da conta</span>
                      <span>↪</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              // Rodapé sem login estilo Gemini Foto 2
              <div className="flex items-center justify-between p-1">
                <button
                  type="button"
                  onClick={dispararLoginGoogle}
                  className="flex items-center gap-2 text-xs font-medium text-[#c4c7c5] hover:text-white transition"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  {sidebarOpen && <span>Fazer login</span>}
                </button>
                <button
                  type="button"
                  onClick={() => setAboutModalOpen(true)}
                  className="text-[#8e918f] hover:text-white p-1"
                  title="Configurações e Sobre"
                >
                  ⚙
                </button>
              </div>
            )}
          </div>
        </aside>

        {/* ================= ÁREA PRINCIPAL ================= */}
        <main className="relative flex flex-1 flex-col overflow-hidden bg-[#131314]">
          {/* Fundo com efeito Glow sutil estilo Gemini */}
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_35%,rgba(26,115,232,0.08),rgba(19,19,20,0))]" />

          {/* Header Superior Estilo Gemini */}
          <header className="relative z-30 flex h-16 shrink-0 items-center justify-between px-4 sm:px-6">
            <div className="flex items-center gap-3">
              {!sidebarOpen && (
                <div className="flex items-center gap-2 cursor-pointer" onClick={novaConversa}>
                  <div className="relative h-7 w-7 overflow-hidden rounded-full ring-1 ring-white/10">
                    <Image src="/logo-helpus.png" alt="HelpUS Logo" fill className="object-cover" />
                  </div>
                  <span className="text-base font-semibold text-white">HelpUS</span>
                </div>
              )}
            </div>

            {/* Ações da Direita do Header */}
            <div className="flex items-center gap-3">
              {profile ? (
                // Header com usuário logado (Avatar + botão Sair)
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setAboutModalOpen(true)}
                    className="hidden sm:inline-flex rounded-full px-3 py-1.5 text-xs text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                  >
                    Sobre o HelpUS
                  </button>

                  <button
                    type="button"
                    onClick={() => setAccountMenuOpen((prev) => !prev)}
                    className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-full ring-2 ring-[#7fcfff]/30 transition hover:ring-[#7fcfff]"
                    title="Menu da conta"
                  >
                    {profile.picture ? (
                      <img src={profile.picture} alt={profile.name} className="h-full w-full object-cover" />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-[#1a73e8] text-xs font-bold text-white">
                        {firstName[0]}
                      </div>
                    )}
                  </button>
                </div>
              ) : (
                // Header sem login estilo Gemini Foto 2
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setAboutModalOpen(true)}
                    className="text-xs font-medium text-[#c4c7c5] hover:text-white transition"
                  >
                    Sobre o HelpUS
                  </button>

                  {/* Botão azul pílula idêntico ao Gemini Foto 2 */}
                  <button
                    type="button"
                    onClick={dispararLoginGoogle}
                    className="rounded-full bg-[#1a73e8] px-5 py-2 text-xs sm:text-sm font-semibold text-white shadow-md hover:bg-[#1557b0] transition"
                  >
                    Fazer login
                  </button>
                </div>
              )}
            </div>
          </header>

          {/* ================= CORPO DO CHAT ================= */}
          <div className="relative z-10 flex flex-1 flex-col overflow-y-auto px-4 pb-32 pt-2">
            {messages.length === 0 ? (
              // ESTADO INICIAL (HERO DO GEMINI)
              <div className="mx-auto flex flex-1 w-full max-w-3xl flex-col items-center justify-center text-center px-2">
                {profile ? (
                  // Saudação personalizada estilo Gemini Foto 4
                  <div className="mb-8">
                    <h1 className="text-3xl sm:text-5xl font-medium tracking-tight text-[#e3e3e3]">
                      Olá, {firstName}
                    </h1>
                    <p className="mt-2 text-lg sm:text-xl font-normal text-[#8e918f]">
                      O que vamos fazer hoje?
                    </p>
                  </div>
                ) : (
                  // Saudação de apresentação estilo Gemini Foto 2
                  <div className="mb-8">
                    <h1 className="text-3xl sm:text-5xl font-medium tracking-tight text-[#e3e3e3]">
                      Conheça o HelpUS, seu assistente pessoal de IA
                    </h1>
                  </div>
                )}

                {/* BARRA DE PROMPT CENTRAL FLUTUANTE ESTILO GEMINI */}
                <div className="w-full">
                  <div className="relative flex flex-col rounded-3xl border border-[#2d2e30] bg-[#1e1f20] p-3 shadow-2xl transition-all focus-within:border-[#1a73e8] focus-within:ring-1 focus-within:ring-[#1a73e8]">
                    {/* Imagem em anexo pré-visualizada */}
                    {selectedImage && (
                      <div className="relative mb-2 inline-block self-start">
                        <img
                          src={selectedImage}
                          alt="Prévia"
                          className="h-20 w-20 rounded-2xl object-cover ring-1 ring-white/20"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedImage(null)
                            setSelectedImageBase64(null)
                          }}
                          className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-rose-600 text-xs font-bold text-white hover:bg-rose-500"
                        >
                          ×
                        </button>
                      </div>
                    )}

                    {/* Textarea */}
                    <textarea
                      ref={inputRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          enviarMensagem()
                        }
                      }}
                      placeholder="Peça ao HelpUS"
                      rows={1}
                      className="w-full resize-none bg-transparent px-3 py-2 text-sm sm:text-base text-[#e3e3e3] placeholder-[#8e918f] outline-none"
                    />

                    {/* Barra de Ações Inferior da Caixa de Input */}
                    <div className="mt-2 flex items-center justify-between pt-1">
                      <div className="flex items-center gap-1">
                        {/* Botão + (Anexar Imagem) */}
                        <input
                          type="file"
                          ref={fileInputRef}
                          accept="image/*"
                          onChange={handleImageUpload}
                          className="hidden"
                        />
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="flex h-9 w-9 items-center justify-center rounded-full text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                          title="Adicionar imagem"
                        >
                          <span className="text-xl leading-none">+</span>
                        </button>

                        {/* Botão Pesquisa Web */}
                        <button
                          type="button"
                          onClick={() => setWebSearchEnabled((prev) => !prev)}
                          className={`flex h-8 items-center gap-1.5 rounded-full px-3 text-xs font-medium transition ${
                            webSearchEnabled
                              ? 'bg-[#004a77] text-[#7fcfff]'
                              : 'text-[#8e918f] hover:bg-[#282a2c] hover:text-white'
                          }`}
                          title="Pesquisa na web em tempo real"
                        >
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                          </svg>
                          <span>Web</span>
                        </button>
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Seletor de Modelo Pílula (Flash-Lite ▾) estilo Gemini */}
                        <div className="relative">
                          <button
                            type="button"
                            onClick={() => setModelDropdownOpen((prev) => !prev)}
                            className="flex items-center gap-1.5 rounded-full bg-[#131314] px-3 py-1.5 text-xs font-medium text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                          >
                            <span>{activeModel.name}</span>
                            <span className="text-[10px] text-[#8e918f]">▾</span>
                          </button>

                          {modelDropdownOpen && (
                            <div className="absolute bottom-10 right-0 z-50 w-52 rounded-2xl border border-[#2d2e30] bg-[#1e1f20] p-1.5 shadow-2xl">
                              {MODEL_OPTIONS.map((m) => (
                                <button
                                  key={m.id}
                                  type="button"
                                  onClick={() => {
                                    setActiveModel(m)
                                    setModelDropdownOpen(false)
                                  }}
                                  className={`flex w-full flex-col rounded-xl px-3 py-2 text-left text-xs transition ${
                                    activeModel.id === m.id
                                      ? 'bg-[#004a77] text-white'
                                      : 'text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white'
                                  }`}
                                >
                                  <span className="font-semibold">{m.name}</span>
                                  <span className="text-[10px] opacity-75">{m.desc}</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Botão Microfone / Chamada de Voz */}
                        <button
                          type="button"
                          onClick={() => {
                            setIsVoiceModalOpen(true)
                            startVoiceRecognition()
                          }}
                          className="flex h-9 w-9 items-center justify-center rounded-full text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                          title="Falar com HelpUS"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 02-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                          </svg>
                        </button>

                        {/* Botão de Envio ↑ */}
                        {(input.trim() || selectedImageBase64) && (
                          <button
                            type="button"
                            onClick={() => enviarMensagem()}
                            className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-zinc-950 font-bold hover:bg-[#e3e3e3] transition shadow-md"
                            title="Enviar"
                          >
                            ↑
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>


              </div>
            ) : (
              // LISTA DE MENSAGENS EM ANDAMENTO ESTILO GEMINI
              <div className="mx-auto w-full max-w-3xl space-y-6">
                {messages.map((msg, idx) => (
                  <div key={idx} className="flex flex-col gap-2">
                    {msg.role === 'user' ? (
                      // Mensagem do Usuário
                      <div className="flex justify-end">
                        <div className="max-w-[85%] rounded-3xl bg-[#282a2c] px-5 py-3 text-sm sm:text-base text-[#e3e3e3]">
                          {msg.image_url && (
                            <img
                              src={msg.image_url}
                              alt="Anexo do usuário"
                              className="mb-2 max-h-60 rounded-xl object-contain"
                            />
                          )}
                          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        </div>
                      </div>
                    ) : (
                      // Resposta da IA (HelpUS)
                      <div className="flex gap-3">
                        <div className="relative mt-1 h-7 w-7 shrink-0 overflow-hidden rounded-full ring-1 ring-white/10">
                          <Image src="/logo-helpus.png" alt="HelpUS Logo" fill className="object-cover" />
                        </div>
                        <div className="min-w-0 flex-1 space-y-2">
                          <div className="text-sm sm:text-base leading-relaxed text-[#e3e3e3]">
                            <MarkdownMessage content={msg.content} />
                          </div>

                          {/* Fontes consultadas na web */}
                          {msg.fontes && msg.fontes.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {msg.fontes.map((f, i) => (
                                <SafeSourceLink key={i} fonte={f} index={i} />
                              ))}
                            </div>
                          )}

                          {/* Barra de Ferramentas da Resposta */}
                          <div className="flex items-center gap-1 pt-1 text-[#8e918f]">
                            <button
                              type="button"
                              onClick={() => copiarTexto(msg.content, idx)}
                              className="flex items-center gap-1 rounded-full p-1.5 text-xs hover:bg-[#282a2c] hover:text-white transition"
                              title="Copiar texto"
                            >
                              <span>{copiedIndex === idx ? '✓ Copiado' : '⧉ Copiar'}</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => ouvirTexto(msg.content)}
                              className="flex items-center gap-1 rounded-full p-1.5 text-xs hover:bg-[#282a2c] hover:text-white transition"
                              title="Ouvir resposta em áudio"
                            >
                              <span>🔊 Ouvir</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Indicador de carregamento */}
                {loading && (
                  <div className="flex gap-3 items-center text-xs text-[#8e918f]">
                    <div className="relative h-6 w-6 overflow-hidden rounded-full ring-1 ring-white/10 animate-pulse">
                      <Image src="/logo-helpus.png" alt="HelpUS Logo" fill className="object-cover" />
                    </div>
                    <span>HelpUS está formulando a resposta...</span>
                  </div>
                )}

                <div ref={messagesEndRef} className="h-6" />
              </div>
            )}
          </div>

          {/* ================= BARRA DE INPUT FIXA INFERIOR (QUANDO HÁ CONVERSA) ================= */}
          {messages.length > 0 && (
            <div className="absolute bottom-6 left-0 right-0 z-30 px-4">
              <div className="mx-auto max-w-3xl">
                <div className="relative flex flex-col rounded-3xl border border-[#2d2e30] bg-[#1e1f20] p-3 shadow-2xl focus-within:border-[#1a73e8]">
                  {selectedImage && (
                    <div className="relative mb-2 inline-block self-start">
                      <img src={selectedImage} alt="Prévia" className="h-16 w-16 rounded-xl object-cover" />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedImage(null)
                          setSelectedImageBase64(null)
                        }}
                        className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] text-white"
                      >
                        ×
                      </button>
                    </div>
                  )}

                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        enviarMensagem()
                      }
                    }}
                    placeholder="Peça ao HelpUS"
                    rows={1}
                    className="w-full resize-none bg-transparent px-3 py-1 text-sm sm:text-base text-[#e3e3e3] placeholder-[#8e918f] outline-none"
                  />

                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white"
                        title="Adicionar imagem"
                      >
                        +
                      </button>
                      <button
                        type="button"
                        onClick={() => setWebSearchEnabled((prev) => !prev)}
                        className={`flex h-7 items-center gap-1 rounded-full px-2.5 text-[11px] font-medium transition ${
                          webSearchEnabled ? 'bg-[#004a77] text-[#7fcfff]' : 'text-[#8e918f] hover:text-white'
                        }`}
                      >
                        Web
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#8e918f]">{activeModel.name}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setIsVoiceModalOpen(true)
                          startVoiceRecognition()
                        }}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-[#c4c7c5] hover:bg-[#282a2c]"
                      >
                        🎙️
                      </button>
                      {(input.trim() || selectedImageBase64) && (
                        <button
                          type="button"
                          onClick={() => enviarMensagem()}
                          className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-zinc-950 font-bold hover:bg-[#e3e3e3]"
                        >
                          ↑
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Disclaimer Inferior Discreto Estilo Gemini */}
          <footer className="absolute bottom-1 left-0 right-0 z-20 text-center text-[11px] text-[#8e918f] pointer-events-none">
            Sujeito aos Termos do HelpUS e à Política de Privacidade. O HelpUS é uma IA e pode cometer erros.
          </footer>
        </main>
      </div>

      {/* ================= MODAL CHAMADA DE VOZ (ESTILO GEMINI LIVE) ================= */}
      {isVoiceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="flex w-full max-w-sm flex-col items-center rounded-3xl border border-white/10 bg-[#1e1f20] p-6 text-center shadow-2xl">
            <div className="relative mb-6 flex h-24 w-24 items-center justify-center">
              <span
                className={`absolute inset-0 rounded-full ${
                  voiceStatus === 'listening'
                    ? 'animate-ping bg-[#1a73e8]/30'
                    : 'bg-[#1a73e8]/10'
                }`}
              />
              <div className="relative z-10 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-tr from-[#1a73e8] to-[#7fcfff] text-2xl shadow-lg">
                🎙️
              </div>
            </div>

            <h3 className="text-lg font-semibold text-white">Voz em Tempo Real</h3>
            <p className="mt-1 text-xs text-[#8e918f]">
              {voiceStatus === 'listening' ? 'Ouvindo você... Fale agora.' : 'Aguardando voz...'}
            </p>

            <div className="my-4 min-h-[50px] w-full rounded-2xl bg-[#131314] p-3 text-xs text-[#c4c7c5]">
              {voiceTranscript || 'Fale no microfone para conversar com o HelpUS...'}
            </div>

            <button
              type="button"
              onClick={() => {
                setIsVoiceModalOpen(false)
                setVoiceStatus('idle')
                if (voiceRecognitionRef.current) voiceRecognitionRef.current.stop()
              }}
              className="rounded-full bg-rose-600 px-6 py-2 text-xs font-semibold text-white hover:bg-rose-500 transition"
            >
              Encerrar
            </button>
          </div>
        </div>
      )}

      {/* ================= MODAL SOBRE O HELPUS ================= */}
      {aboutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-3xl border border-[#2d2e30] bg-[#1e1f20] p-6 shadow-2xl">
            <div className="flex items-center gap-3 border-b border-white/5 pb-4">
              <div className="relative h-10 w-10 overflow-hidden rounded-full ring-1 ring-white/10">
                <Image src="/logo-helpus.png" alt="HelpUS Logo" fill className="object-cover" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">HelpUS AI</h3>
                <p className="text-xs text-[#8e918f]">Assistente Pessoal de Inteligência Artificial</p>
              </div>
            </div>

            <div className="my-4 space-y-3 text-xs leading-relaxed text-[#c4c7c5]">
              <p>
                O <strong>HelpUS AI</strong> é a plataforma proprietária de inteligência artificial da HelpUS, projetada para proporcionar respostas inteligentes, raciocínio aprofundado e automação operacional.
              </p>
              <div className="rounded-2xl bg-[#131314] p-3 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-[#8e918f]">Versão:</span>
                  <span className="text-white font-medium">1.0.0 (Gemini Interface)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8e918f]">Provedor Padrão:</span>
                  <span className="text-white font-medium">Google Gemini 2.5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8e918f]">Status da Nuvem:</span>
                  <span className="text-emerald-400 font-medium">● Online (Vercel + Railway)</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setAboutModalOpen(false)}
                className="rounded-full bg-white/10 px-5 py-2 text-xs font-semibold text-white hover:bg-white/20 transition"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
