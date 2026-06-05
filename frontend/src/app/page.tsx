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
  const [pesquisarWeb, setPesquisarWeb] = useState(false)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const enviarMensagem = async () => {
    const texto = input.trim()
    if (!texto || loading) return

    setMessages(prev => [...prev, { role: 'user', content: texto }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Erro ao conectar com o servidor: ${message}`,
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
                Pergunte algo ao HelpUS. Ligue a pesquisa na web quando precisar de informacoes externas.
              </p>
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
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <article
                  className={`max-w-[92%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[78%] ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'border border-slate-200 bg-white text-slate-900'
                  }`}
                >
                  <div className={`mb-1 text-sm font-bold ${msg.role === 'user' ? 'text-blue-50' : 'text-slate-900'}`}>
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
              placeholder="Digite sua pergunta... Enter para enviar, Shift+Enter para nova linha"
              className="min-h-[48px] flex-1 resize-none rounded-xl border border-slate-300 p-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              rows={1}
              disabled={loading}
            />
            <button
              onClick={enviarMensagem}
              disabled={loading || !input.trim()}
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
