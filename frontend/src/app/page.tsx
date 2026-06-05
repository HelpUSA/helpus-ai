'use client'
import { useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  fontes?: { titulo: string; url: string; fonte: string }[]
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [pesquisarWeb, setPesquisarWeb] = useState(true)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const enviarMensagem = async () => {
    if (!input.trim() || loading) return

    const novaMsg: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, novaMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensagem: input,
          session_id: sessionId || undefined,
          pesquisar_web: pesquisarWeb,
        }),
      })

      const data = await response.json()
      
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.resposta,
          fontes: data.fontes,
        },
      ])
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '? Erro ao conectar com o servidor. Verifique se a API está rodando.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const limparChat = () => {
    setMessages([])
    setSessionId('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      enviarMensagem()
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Header */}
      <header className="bg-white shadow-sm p-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">?? HelpUS</h1>
          <p className="text-sm text-gray-500">Seu Assistente Inteligente</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={pesquisarWeb}
              onChange={(e) => setPesquisarWeb(e.target.checked)}
              className="rounded"
            />
            ?? Pesquisar na web
          </label>
          <button
            onClick={limparChat}
            className="text-sm text-gray-500 hover:text-red-500"
            title="Limpar conversa"
          >
            ??? Nova conversa
          </button>
        </div>
      </header>

      {/* Área de mensagens */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-4xl mb-4">??</p>
            <p className="text-lg">Olá! Como posso ajudar?</p>
            <p className="text-sm mt-2">
              Digite sua pergunta abaixo para começar.
            </p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white shadow-sm border border-gray-200'
              }`}
            >
              <div className="font-bold text-sm mb-1">
                {msg.role === 'user' ? '?? Você' : '?? Assistente'}
              </div>
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {msg.content}
              </div>
              
              {/* Fontes da pesquisa */}
              {msg.fontes && msg.fontes.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-300">
                  <p className="text-xs font-semibold text-gray-500 mb-1">
                    ?? Fontes consultadas:
                  </p>
                  {msg.fontes.map((fonte, i) => (
                    <a
                      key={i}
                      href={fonte.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-blue-600 hover:underline truncate"
                    >
                      {i + 1}. {fonte.titulo} ({fonte.fonte})
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Indicador de carregamento */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white shadow-sm border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="animate-pulse flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                </div>
                <span className="text-sm text-gray-500">Pensando...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={(el) => el?.scrollIntoView({ behavior: 'smooth' })} />
      </div>

      {/* Input de mensagem */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Digite sua pergunta... (Enter para enviar, Shift+Enter para nova linha)"
            className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            rows={1}
            disabled={loading}
          />
          <button
            onClick={enviarMensagem}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm transition-colors"
          >
            {loading ? '...' : 'Enviar'}
          </button>
        </div>
        {sessionId && (
          <p className="text-xs text-gray-400 mt-2">
            Sessão: {sessionId.slice(0, 8)}...
          </p>
        )}
      </div>
    </div>
  )
}

