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
  file_name?: string
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

interface Projeto {
  project_id: string
  nome: string
  descricao?: string
  instrucoes?: string
  created_at?: string
}

interface AttachedFile {
  name: string
  size: number
  type: string
  isImage: boolean
  previewUrl?: string
  base64?: string
  textContent?: string
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

  // Upload de arquivos e imagens (multimodal)
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [selectedImageBase64, setSelectedImageBase64] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Projetos & Renomeação de conversas
  const [projetos, setProjetos] = useState<Projeto[]>([
    { project_id: 'general', nome: 'Geral', descricao: 'Conversas gerais da HelpUS' },
  ])
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all')
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [isNovoProjetoOpen, setIsNovoProjetoOpen] = useState(false)
  const [novoProjetoNome, setNovoProjetoNome] = useState('')
  const [novoProjetoDesc, setNovoProjetoDesc] = useState('')

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

  // Carrega token salvo, projetos e conversas
  useEffect(() => {
    const savedToken = window.localStorage.getItem('helpus_google_token') || ''
    if (savedToken) {
      setGoogleToken(savedToken)
      setProfile(decodeJwtProfile(savedToken))
      carregarConversas(savedToken)
      carregarProjetos(savedToken)
    } else {
      carregarProjetos()
      try {
        const loc = window.localStorage.getItem('helpus_conversas_locais')
        if (loc) setConversas(JSON.parse(loc))
      } catch {}
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

  // Carregar projetos disponíveis
  const carregarProjetos = async (token = googleToken) => {
    try {
      const res = await fetch(`${apiUrl}/projetos`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.ok) {
        const data = await res.json()
        if (data.projetos && Array.isArray(data.projetos)) {
          setProjetos(data.projetos)
        }
      }
    } catch {}
  }

  // Criar novo projeto
  const criarNovoProjeto = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!novoProjetoNome.trim()) return
    const pid = `proj_${Date.now()}`
    const novo: Projeto = {
      project_id: pid,
      nome: novoProjetoNome.trim(),
      descricao: novoProjetoDesc.trim(),
    }
    setProjetos((prev) => [...prev, novo])
    setSelectedProjectId(pid)
    setIsNovoProjetoOpen(false)
    setNovoProjetoNome('')
    setNovoProjetoDesc('')
    try {
      await fetch(`${apiUrl}/projetos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(googleToken ? { Authorization: `Bearer ${googleToken}` } : {}),
        },
        body: JSON.stringify(novo),
      })
    } catch {}
    novaConversa()
  }

  // Carregar histórico de conversas do usuário
  const carregarConversas = async (token = googleToken, projId = selectedProjectId) => {
    try {
      const url = projId && projId !== 'all' ? `${apiUrl}/conversas?project_id=${projId}` : `${apiUrl}/conversas`
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.ok) {
        const data = await res.json()
        const lista = Array.isArray(data) ? data : data.conversas || []
        if (lista.length > 0) {
          setConversas(lista)
          try {
            window.localStorage.setItem('helpus_conversas_locais', JSON.stringify(lista))
          } catch {}
        } else {
          try {
            const loc = window.localStorage.getItem('helpus_conversas_locais')
            if (loc) setConversas(JSON.parse(loc))
          } catch {}
        }
      }
    } catch {
      try {
        const loc = window.localStorage.getItem('helpus_conversas_locais')
        if (loc) setConversas(JSON.parse(loc))
      } catch {}
    }
  }

  // Carregar conversa específica
  const abrirConversa = async (id: string) => {
    try {
      setLoading(true)
      setSessionId(id)
      const res = await fetch(`${apiUrl}/historico/${id}`, {
        headers: googleToken ? { Authorization: `Bearer ${googleToken}` } : {},
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
    setAttachedFile(null)
    inputRef.current?.focus()
  }

  // Excluir conversa
  const excluirConversa = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setConversas((prev) => {
      const atualizadas = prev.filter((c) => c.session_id !== id)
      try {
        window.localStorage.setItem('helpus_conversas_locais', JSON.stringify(atualizadas))
      } catch {}
      return atualizadas
    })
    if (sessionId === id) novaConversa()

    try {
      await fetch(`${apiUrl}/conversa/${id}`, {
        method: 'DELETE',
        headers: googleToken ? { Authorization: `Bearer ${googleToken}` } : {},
      })
    } catch {}
  }

  // Renomear conversa
  const salvarRenomeacao = async (id: string) => {
    const novoTitulo = editingTitle.trim()
    if (!novoTitulo) {
      setEditingSessionId(null)
      return
    }
    setConversas((prev) => {
      const atualizadas = prev.map((c) => (c.session_id === id ? { ...c, titulo: novoTitulo } : c))
      try {
        window.localStorage.setItem('helpus_conversas_locais', JSON.stringify(atualizadas))
      } catch {}
      return atualizadas
    })
    setEditingSessionId(null)
    try {
      await fetch(`${apiUrl}/conversa/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(googleToken ? { Authorization: `Bearer ${googleToken}` } : {}),
        },
        body: JSON.stringify({ titulo: novoTitulo }),
      })
    } catch {}
  }

  // Filtro de conversas por busca e por projeto
  const conversasFiltradas = conversas.filter((c) => {
    const matchBusca = (c.titulo || '').toLowerCase().includes(searchQuery.toLowerCase())
    if (!matchBusca) return false
    if (selectedProjectId === 'all') return true
    if (selectedProjectId === 'general') return !c.project_id || c.project_id === 'general'
    return c.project_id === selectedProjectId
  })

  // Enviar mensagem para a IA
  const enviarMensagem = async (texto = input) => {
    const textoLimpo = texto.trim()
    if (!textoLimpo && !selectedImageBase64 && !attachedFile) return
    if (loading) return

    // Se não estiver logado, dispara login oficial estilo Gemini
    if (!googleToken) {
      dispararLoginGoogle()
      return
    }

    let textoFinal = textoLimpo
    let imagemBase64ParaEnvio: string | undefined = selectedImageBase64 || undefined
    let imagemPreviewUrl: string | undefined = selectedImage || undefined
    let documentoNome: string | undefined = undefined

    if (attachedFile) {
      if (attachedFile.isImage) {
        imagemBase64ParaEnvio = attachedFile.base64
        imagemPreviewUrl = attachedFile.previewUrl
      } else if (attachedFile.type === 'application/pdf' && attachedFile.base64) {
        imagemBase64ParaEnvio = attachedFile.base64
        documentoNome = attachedFile.name
        if (!textoFinal) textoFinal = `Por favor, analise este documento PDF (${attachedFile.name}) e resuma seus pontos principais.`
      } else if (attachedFile.textContent) {
        textoFinal += `\n\n[Documento Anexado: ${attachedFile.name}]\n\`\`\`\n${attachedFile.textContent}\n\`\`\``
        documentoNome = attachedFile.name
      } else {
        documentoNome = attachedFile.name
      }
    }

    const currentSessionId = sessionId || `sess_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
    if (!sessionId) setSessionId(currentSessionId)

    // Otimisticamente adiciona conversa à lista de Recentes
    setConversas((prev) => {
      const existe = prev.some((c) => c.session_id === currentSessionId)
      if (existe) return prev
      const nova: ConversaResumo = {
        session_id: currentSessionId,
        titulo: (textoLimpo || attachedFile?.name || 'Nova conversa').slice(0, 45),
        updated_at: new Date().toISOString(),
        total_mensagens: 1,
        project_id: selectedProjectId === 'all' ? 'general' : selectedProjectId,
      }
      const lista = [nova, ...prev]
      try {
        window.localStorage.setItem('helpus_conversas_locais', JSON.stringify(lista))
      } catch {}
      return lista
    })

    setInput('')
    setSelectedImage(null)
    setSelectedImageBase64(null)
    setAttachedFile(null)

    const novaMensagemUsuario: Message = {
      role: 'user',
      content: textoLimpo || (attachedFile ? `Analisar anexo: ${attachedFile.name}` : ''),
      image_url: imagemPreviewUrl,
      file_name: documentoNome,
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

      const authHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (googleToken && googleToken !== 'null' && googleToken !== 'undefined') {
        authHeaders['Authorization'] = `Bearer ${googleToken}`
      }

      // Tenta rota SSE /chat/stream
      const resStream = await fetch(`${apiUrl}/chat/stream`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          mensagem: textoFinal,
          session_id: currentSessionId,
          pesquisar_web: webSearchEnabled,
          imagem_base64: imagemBase64ParaEnvio,
          model: activeModel.id,
          project_id: selectedProjectId === 'all' ? 'general' : selectedProjectId,
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
              if (!dataStr || dataStr === '[DONE]') continue
              try {
                const parsed = JSON.parse(dataStr)
                const chunkText = parsed.content ?? parsed.text ?? parsed.chunk ?? ''
                if (chunkText) {
                  respostaAcumulada += chunkText
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
        if (respostaAcumulada.trim().length > 0) {
          carregarConversas(googleToken)
          return
        }
      }

      // Fallback padrão /chat síncrono
      const res = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          mensagem: textoFinal,
          session_id: currentSessionId,
          pesquisar_web: webSearchEnabled,
          imagem_base64: imagemBase64ParaEnvio,
          model: activeModel.id,
          project_id: selectedProjectId === 'all' ? 'general' : selectedProjectId,
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
        throw new Error('Falha no endpoint /chat')
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return
      setMessages((prev) => {
        const copia = [...prev]
        copia[copia.length - 1] = {
          role: 'assistant',
          content: 'Desculpe, ocorreu uma instabilidade momentânea ao processar sua solicitação.',
        }
        return copia
      })
    } finally {
      setLoading(false)
    }
  }

  // Upload de Arquivos e Imagens
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const isImage = file.type.startsWith('image/')
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    const isTextDoc = /\.(txt|md|csv|json|js|ts|py|sql|html|css|log|env|xml|yaml|yml)$/i.test(file.name)

    if (isImage) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const result = event.target?.result as string
        if (result) {
          setAttachedFile({
            name: file.name,
            size: file.size,
            type: file.type,
            isImage: true,
            previewUrl: result,
            base64: result.split(',')[1] || '',
          })
          setSelectedImage(result)
          setSelectedImageBase64(result.split(',')[1] || '')
        }
      }
      reader.readAsDataURL(file)
    } else if (isPdf) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const result = event.target?.result as string
        if (result) {
          setAttachedFile({
            name: file.name,
            size: file.size,
            type: 'application/pdf',
            isImage: false,
            base64: result,
          })
          setSelectedImage(null)
          setSelectedImageBase64(result)
        }
      }
      reader.readAsDataURL(file)
    } else if (isTextDoc) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const text = event.target?.result as string
        if (text) {
          setAttachedFile({
            name: file.name,
            size: file.size,
            type: file.type || 'text/plain',
            isImage: false,
            textContent: text,
          })
          setSelectedImage(null)
          setSelectedImageBase64(null)
        }
      }
      reader.readAsText(file)
    } else {
      const reader = new FileReader()
      reader.onload = (event) => {
        const result = event.target?.result as string
        setAttachedFile({
          name: file.name,
          size: file.size,
          type: file.type || 'application/octet-stream',
          isImage: false,
          base64: result ? result.split(',')[1] : '',
        })
        setSelectedImage(null)
        setSelectedImageBase64(null)
      }
      reader.readAsDataURL(file)
    }

    e.target.value = ''
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                  <span>Anexar arquivos e imagens</span>
                </button>
              </div>

              {/* Seletor de Projetos */}
              <div className="mb-2">
                <div className="flex items-center justify-between px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[#8e918f]">
                  <span>Projetos</span>
                  <button
                    type="button"
                    onClick={() => setIsNovoProjetoOpen(true)}
                    className="text-[#7fcfff] hover:underline normal-case text-xs font-medium"
                    title="Criar novo projeto"
                  >
                    + Novo
                  </button>
                </div>
                <div className="flex flex-wrap gap-1 px-1 py-1">
                  <button
                    type="button"
                    onClick={() => setSelectedProjectId('all')}
                    className={`rounded-lg px-2.5 py-1 text-xs transition ${
                      selectedProjectId === 'all'
                        ? 'bg-[#004a77] text-white font-medium'
                        : 'bg-[#131314] text-[#8e918f] hover:bg-[#282a2c] hover:text-white'
                    }`}
                  >
                    Todos
                  </button>
                  {projetos.map((proj) => (
                    <button
                      key={proj.project_id}
                      type="button"
                      onClick={() => setSelectedProjectId(proj.project_id)}
                      className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs transition ${
                        selectedProjectId === proj.project_id
                          ? 'bg-[#004a77] text-white font-medium'
                          : 'bg-[#131314] text-[#8e918f] hover:bg-[#282a2c] hover:text-white'
                      }`}
                      title={proj.descricao || proj.nome}
                    >
                      <span>📁</span>
                      <span className="max-w-[85px] truncate">{proj.nome}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Se NÃO logado: Card Informativo do Gemini */}
              {!googleToken && (
                <div className="my-2 rounded-2xl border border-white/5 bg-[#131314] p-3 text-xs text-[#c4c7c5]">
                  <div className="flex items-start gap-2">
                    <span className="text-[#7fcfff]">ⓘ</span>
                    <div>
                      <span>Faça login para salvar suas conversas na nuvem.</span>
                      <button
                        type="button"
                        onClick={dispararLoginGoogle}
                        className="mt-1 block font-semibold text-[#7fcfff] underline hover:text-[#a8e0ff]"
                      >
                        Fazer login agora
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Lista de Recentes estilo Gemini com Renomear e Excluir */}
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
                    const isEditing = editingSessionId === conv.session_id

                    if (isEditing) {
                      return (
                        <div key={conv.session_id} className="flex items-center gap-1 rounded-xl bg-[#282a2c] p-1 text-xs">
                          <input
                            type="text"
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') salvarRenomeacao(conv.session_id)
                              if (e.key === 'Escape') setEditingSessionId(null)
                            }}
                            className="flex-1 rounded-lg bg-[#131314] px-2 py-1 text-xs text-white border border-[#7fcfff] outline-none"
                            autoFocus
                          />
                          <button
                            type="button"
                            onClick={() => salvarRenomeacao(conv.session_id)}
                            className="p-1 text-xs text-emerald-400 hover:text-emerald-300"
                            title="Salvar novo título"
                          >
                            ✓
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingSessionId(null)}
                            className="p-1 text-xs text-[#8e918f] hover:text-white"
                            title="Cancelar"
                          >
                            ✕
                          </button>
                        </div>
                      )
                    }

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
                        <span className="truncate pr-2 flex-1">{titulo}</span>
                        <div className="hidden shrink-0 items-center gap-1 group-hover:flex">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditingSessionId(conv.session_id)
                              setEditingTitle(conv.titulo)
                            }}
                            className="text-[#8e918f] hover:text-[#7fcfff] p-0.5 transition"
                            title="Renomear conversa"
                          >
                            ✏️
                          </button>
                          <button
                            type="button"
                            onClick={(e) => excluirConversa(conv.session_id, e)}
                            className="text-[#8e918f] hover:text-rose-400 p-0.5 transition font-bold"
                            title="Excluir conversa"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
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

          {/* ================= CORPO DO CHAT / SPARK ================= */}
          <div className="relative z-10 flex flex-1 flex-col overflow-y-auto px-4 pb-32 pt-2">
            {activeTab === 'spark' ? (
              <div className="mx-auto flex h-full w-full max-w-4xl flex-col overflow-y-auto px-4 py-6 sm:px-6">
                <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/5 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-2xl font-bold text-white">Spark</h2>
                      <span className="rounded bg-[#004a77] px-2 py-0.5 text-[11px] font-bold text-[#7fcfff]">BETA</span>
                    </div>
                    <p className="mt-1 text-xs text-[#8e918f]">
                      Espaço experimental da HelpUS para Projetos dedicados, Agentes Especializados e Ideação Contínua.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsNovoProjetoOpen(true)}
                    className="flex items-center gap-2 rounded-full bg-[#004a77] px-4 py-2 text-xs font-semibold text-[#7fcfff] hover:bg-[#005a92] transition self-start sm:self-auto shadow"
                  >
                    <span>+</span> Novo Projeto
                  </button>
                </div>

                {/* Seção 1: Workspaces de Projetos */}
                <div className="mb-8">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-[#c4c7c5]">
                      Workspaces de Projetos ({projetos.length})
                    </h3>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                    {projetos.map((proj) => {
                      const totalConvs = conversas.filter((c) =>
                        proj.project_id === 'general' ? !c.project_id || c.project_id === 'general' : c.project_id === proj.project_id
                      ).length
                      const isAtivo = selectedProjectId === proj.project_id
                      return (
                        <div
                          key={proj.project_id}
                          className={`flex flex-col justify-between rounded-2xl border p-4 transition ${
                            isAtivo
                              ? 'border-[#7fcfff]/50 bg-[#1e1f20] ring-1 ring-[#7fcfff]/30'
                              : 'border-white/5 bg-[#131314] hover:border-white/10 hover:bg-[#1e1f20]'
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between">
                              <span className="text-2xl">📁</span>
                              <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-[#8e918f]">
                                {totalConvs} {totalConvs === 1 ? 'conversa' : 'conversas'}
                              </span>
                            </div>
                            <h4 className="mt-2 text-sm font-semibold text-white">{proj.nome}</h4>
                            <p className="mt-1 text-xs text-[#8e918f] line-clamp-2">
                              {proj.descricao || 'Conversas e memórias dedicadas para este projeto.'}
                            </p>
                          </div>

                          <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedProjectId(proj.project_id)
                                setActiveTab('chat')
                              }}
                              className="text-xs font-semibold text-[#7fcfff] hover:underline"
                            >
                              Abrir no Chat →
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedProjectId(proj.project_id)
                                setActiveTab('chat')
                                novaConversa()
                              }}
                              className="rounded-lg bg-white/5 px-2.5 py-1 text-[11px] text-[#c4c7c5] hover:bg-white/10"
                            >
                              + Nova conversa
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Seção 2: Agentes Especializados Spark */}
                <div>
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#c4c7c5]">
                    Agentes Especializados (Gems / Spark)
                  </h3>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div
                      onClick={() => {
                        setActiveTab('chat')
                        setInput('Atuar como Agente Especialista em Código e Arquitetura de Software: ')
                        inputRef.current?.focus()
                      }}
                      className="cursor-pointer rounded-2xl border border-white/5 bg-[#131314] p-4 transition hover:border-[#7fcfff]/30 hover:bg-[#1e1f20]"
                    >
                      <span className="text-xl">⚡</span>
                      <h4 className="mt-2 text-sm font-semibold text-white">Engenheiro & Arquiteto</h4>
                      <p className="mt-1 text-xs text-[#8e918f]">
                        Foco em depuração, análise de código, APIs e arquitetura de software.
                      </p>
                    </div>

                    <div
                      onClick={() => {
                        setActiveTab('chat')
                        setInput('Atuar como Agente Redator Executivo da HelpUS: ')
                        inputRef.current?.focus()
                      }}
                      className="cursor-pointer rounded-2xl border border-white/5 bg-[#131314] p-4 transition hover:border-[#7fcfff]/30 hover:bg-[#1e1f20]"
                    >
                      <span className="text-xl">✍️</span>
                      <h4 className="mt-2 text-sm font-semibold text-white">Redator Executivo</h4>
                      <p className="mt-1 text-xs text-[#8e918f]">
                        Criação de propostas, e-mails executivos, contratos e relatórios claros.
                      </p>
                    </div>

                    <div
                      onClick={() => {
                        setActiveTab('chat')
                        setInput('Atuar como Analista de Documentos e Planilhas: ')
                        inputRef.current?.focus()
                      }}
                      className="cursor-pointer rounded-2xl border border-white/5 bg-[#131314] p-4 transition hover:border-[#7fcfff]/30 hover:bg-[#1e1f20]"
                    >
                      <span className="text-xl">📊</span>
                      <h4 className="mt-2 text-sm font-semibold text-white">Analista de Documentos</h4>
                      <p className="mt-1 text-xs text-[#8e918f]">
                        Extração de insights, resumos de PDFs, planilhas CSV e tabelas de dados.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : messages.length === 0 ? (
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
                    {/* Anexo pré-visualizado (Imagem ou Documento) */}
                    {attachedFile && (
                      <div className="relative mb-2 inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-[#282a2c] p-2 text-xs text-[#e3e3e3] shadow-md self-start">
                        {attachedFile.isImage && attachedFile.previewUrl ? (
                          <img src={attachedFile.previewUrl} alt="Prévia" className="h-14 w-14 rounded-xl object-cover" />
                        ) : (
                          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#004a77] text-lg text-[#7fcfff]">
                            📄
                          </div>
                        )}
                        <div className="flex flex-col pr-6">
                          <span className="max-w-[220px] truncate font-medium">{attachedFile.name}</span>
                          <span className="text-[10px] text-[#8e918f]">
                            {(attachedFile.size / 1024).toFixed(1)} KB {attachedFile.isImage ? '• Imagem' : '• Documento'}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setAttachedFile(null)
                            setSelectedImage(null)
                            setSelectedImageBase64(null)
                          }}
                          className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-rose-600 text-xs font-bold text-white hover:bg-rose-500 shadow"
                          title="Remover anexo"
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
                        {/* Botão + (Anexar Arquivo ou Imagem) */}
                        <input
                          type="file"
                          ref={fileInputRef}
                          accept="image/*,application/pdf,.txt,.md,.csv,.json,.doc,.docx,.xlsx,.xls"
                          onChange={handleFileUpload}
                          className="hidden"
                        />
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="flex h-9 w-9 items-center justify-center rounded-full text-[#c4c7c5] hover:bg-[#282a2c] hover:text-white transition"
                          title="Anexar imagem ou documento (PDF, DOCX, TXT, CSV, etc.)"
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
                        {(input.trim() || selectedImageBase64 || attachedFile) && (
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
                          {msg.file_name && (
                            <div className="mb-2 inline-flex items-center gap-2 rounded-xl bg-white/10 px-3 py-1.5 text-xs text-[#c4c7c5]">
                              <span>📄</span>
                              <span className="font-medium text-white">{msg.file_name}</span>
                            </div>
                          )}
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
                  {/* Anexo pré-visualizado (Imagem ou Documento) */}
                  {attachedFile && (
                    <div className="relative mb-2 inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-[#282a2c] p-2 text-xs text-[#e3e3e3] shadow-md self-start">
                      {attachedFile.isImage && attachedFile.previewUrl ? (
                        <img src={attachedFile.previewUrl} alt="Prévia" className="h-12 w-12 rounded-xl object-cover" />
                      ) : (
                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#004a77] text-base text-[#7fcfff]">
                          📄
                        </div>
                      )}
                      <div className="flex flex-col pr-5">
                        <span className="max-w-[180px] truncate font-medium">{attachedFile.name}</span>
                        <span className="text-[10px] text-[#8e918f]">
                          {(attachedFile.size / 1024).toFixed(1)} KB {attachedFile.isImage ? '• Imagem' : '• Documento'}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setAttachedFile(null)
                          setSelectedImage(null)
                          setSelectedImageBase64(null)
                        }}
                        className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white hover:bg-rose-500 shadow"
                        title="Remover anexo"
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
                        title="Anexar imagem ou documento"
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
                      {(input.trim() || selectedImageBase64 || attachedFile) && (
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

      {/* ================= MODAL NOVO PROJETO ================= */}
      {isNovoProjetoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-3xl border border-[#2d2e30] bg-[#1e1f20] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[#004a77] text-base text-[#7fcfff]">
                  📁
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Criar Novo Projeto</h3>
                  <p className="text-xs text-[#8e918f]">Organize chats, documentos e instruções</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsNovoProjetoOpen(false)}
                className="text-[#8e918f] hover:text-white transition text-lg"
              >
                ×
              </button>
            </div>

            <form onSubmit={criarNovoProjeto} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#c4c7c5] mb-1">
                  Nome do Projeto *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Suporte Técnico, Auditoria Fiscal, Sistema..."
                  value={novoProjetoNome}
                  onChange={(e) => setNovoProjetoNome(e.target.value)}
                  className="w-full rounded-2xl border border-[#2d2e30] bg-[#131314] px-4 py-2.5 text-xs text-white placeholder-[#8e918f] outline-none focus:border-[#7fcfff] transition"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#c4c7c5] mb-1">
                  Descrição ou Objetivo (opcional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Contexto e diretrizes específicas que a IA deve lembrar neste projeto..."
                  value={novoProjetoDesc}
                  onChange={(e) => setNovoProjetoDesc(e.target.value)}
                  className="w-full resize-none rounded-2xl border border-[#2d2e30] bg-[#131314] px-4 py-2 text-xs text-white placeholder-[#8e918f] outline-none focus:border-[#7fcfff] transition"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/5">
                <button
                  type="button"
                  onClick={() => setIsNovoProjetoOpen(false)}
                  className="rounded-full bg-white/5 px-4 py-2 text-xs font-medium text-[#c4c7c5] hover:bg-white/10 transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={!novoProjetoNome.trim()}
                  className="rounded-full bg-[#1a73e8] px-5 py-2 text-xs font-medium text-white hover:bg-[#1558b0] transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                >
                  Criar Projeto
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
