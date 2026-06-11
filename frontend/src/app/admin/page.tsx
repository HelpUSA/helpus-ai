'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

interface StatusData {
  status?: string
  modelo?: string
  modelo_carregado?: boolean
  paginas_indexadas?: number
  app_version?: string
  build_commit?: string
  auth_required?: boolean
  provider_order?: string[]
}

export default function AdminPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const [statusData, setStatusData] = useState<StatusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState('')

  useEffect(() => {
    let mounted = true

    const carregarStatus = async () => {
      try {
        setLoading(true)
        setErro('')
        const response = await fetch(`${apiUrl}/status`, { cache: 'no-store' })
        const data = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(data?.detail || `Erro HTTP ${response.status}`)
        if (mounted) setStatusData(data)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Erro desconhecido'
        if (mounted) setErro(message)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    carregarStatus()
    return () => {
      mounted = false
    }
  }, [apiUrl])

  const cards = [
    ['Status', statusData?.status || (loading ? 'Carregando' : 'Indisponivel')],
    ['Modelo', statusData?.modelo || 'Nao informado'],
    ['IA carregada', statusData?.modelo_carregado ? 'Sim' : 'Nao'],
    ['Paginas indexadas', String(statusData?.paginas_indexadas ?? 0)],
    ['Versao', statusData?.app_version || 'Nao informado'],
    ['Autenticacao', statusData?.auth_required ? 'Obrigatoria' : 'Nao obrigatoria'],
  ]

  return (
    <main className="min-h-screen bg-[#212121] px-4 py-6 text-zinc-100">
      <div className="mx-auto flex min-h[calc(100vh-3rem)] w-full max-w-5xl flex-col justify-center">
        <div className="rounded-3xl border border-white/10 bg-zinc-950/60 p-8 shadow-2xl shadow-black/30">
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="mb-3 text-sm font-medium text-zinc-400">HelpUS</p>
              <h1 className="text-3xl font-semibold tracking-tight text-white">Painel operacional</h1>
              <p className="mt-3 max-w-2xl text-base leading-7 text-zinc-400">
                Visao interna com status da API, modelo, autenticacao e indice de paginas.
              </p>
            </div>
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-full bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200"
            >
              Voltar ao chat
            </Link>
          </div>

          {erro && (
            <div className="mb-6 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm leading-6 text-rose-100">
              Nao foi possivel carregar o status: {erro}
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {cards.map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{label}</p>
                <p className="mt-2 break-words text-lg font-medium text-zinc-100">{value}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="font-medium text-zinc-100">Provedores de IA</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                {(statusData?.provider_order || []).length > 0
                  ? statusData?.provider_order?.join(' -> ')
                  : 'Nenhum provedor informado pelo backend.'}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="font-medium text-zinc-100">Build</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                Commit: {statusData?.build_commit || 'Nao informado'}
              </p>
              <p className="mt-1 text-xs text-zinc-500">
                Fonte de dados: {apiUrl}/status
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center justify-center rounded-full border border-white/10 px-5 py-3 text-sm font-semibold text-zinc-200 transition hover:bg-white/10"
            >
              Atualizar painel
            </button>
            <span className="inline-flex items-center justify-center rounded-full border border-white/10 px-5 py-3 text-sm text-zinc-400">
              {loading ? 'Carregando status...' : 'Status carregado'}
            </span>
          </div>
        </div>
      </div>
    </main>
  )
}
