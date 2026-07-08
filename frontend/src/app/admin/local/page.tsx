'use client'

// Contrato: máximo 5 comandos, 240 caracteres por comando Nenhum comando é executado por este painel.

import Link from 'next/link'
import { useCallback, useEffect, useState } from 'react'

type JsonObject = Record<string, unknown>

interface LocalFileEntry {
  path: string
  size: number
}

interface LocalFilesResult {
  ok?: boolean
  path?: string
  files?: LocalFileEntry[]
  truncated?: boolean
  reason?: string
}

interface LocalSearchMatch {
  path: string
  line: number
  text: string
}

interface LocalSearchResult {
  ok?: boolean
  query?: string
  path?: string
  matches?: LocalSearchMatch[]
  scanned_files?: number
  truncated?: boolean
  reason?: string
}

interface LocalPlanResult {
  ok?: boolean
  mode?: string
  executed?: boolean
  allowed?: boolean
  risk?: string
  reason?: string
  intent?: string
  commands?: string[]
  blocked_reasons?: string[]
  requires_human_confirmation?: boolean
}

interface LocalSnapshot {
  status: JsonObject | null
  diff: JsonObject | null
  files: LocalFilesResult | null
  search: LocalSearchResult | null
  phaseAPlan: LocalPlanResult | null
  blockedPlan: LocalPlanResult | null
}

function decodeJwtEmail(token: string) {
  try {
    const payload = token.split('.')[1]
    if (!payload) return ''
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return String(decoded.email || '').toLowerCase()
  } catch {
    return ''
  }
}

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2)
}

function findProposalId(value: unknown): string {
  if (!value || typeof value !== 'object') return ''
  const record = value as Record<string, unknown>
  const direct = record.proposal_id
  if (typeof direct === 'string' && direct.trim()) return direct

  const proposal = record.proposal
  if (proposal && typeof proposal === 'object') {
    const nested = (proposal as Record<string, unknown>).proposal_id
    if (typeof nested === 'string' && nested.trim()) return nested
  }

  const proposals = record.proposals
  if (Array.isArray(proposals)) {
    for (const item of proposals) {
      const candidate = findProposalId(item)
      if (candidate) return candidate
    }
  }

  return ''
}

function RiskBadge({ plan }: { plan: LocalPlanResult | null }) {
  const risk = plan?.risk || 'unknown'
  const label = plan?.allowed ? 'permitido para planejar' : risk === 'blocked' ? 'bloqueado' : 'revisão necessária'
  const className = plan?.allowed
    ? 'border-emerald-700 bg-emerald-950/50 text-emerald-200'
    : risk === 'blocked'
      ? 'border-red-700 bg-red-950/50 text-red-200'
      : 'border-amber-700 bg-amber-950/50 text-amber-200'
  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${className}`}>{label}</span>
}

export default function AdminLocalReadonlyPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const adminEmails = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || '')
    .split(',')
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean)

  const [googleToken, setGoogleToken] = useState('')
  const [profileEmail, setProfileEmail] = useState('')
  const [snapshot, setSnapshot] = useState<LocalSnapshot>({
    status: null,
    diff: null,
    files: null,
    search: null,
    phaseAPlan: null,
    blockedPlan: null,
  })
  const [customIntent, setCustomIntent] = useState('phase_b_validation')
  const [customCommand, setCustomCommand] = useState('git diff --check')
  const [customPlan, setCustomPlan] = useState<LocalPlanResult | null>(null)
  const [planning, setPlanning] = useState(false)
  const [proposalNote, setProposalNote] = useState('phase-c ui proposal')
  const [proposalResult, setProposalResult] = useState<unknown>(null)
  const [proposals, setProposals] = useState<unknown>(null)
  const [proposalIntegrity, setProposalIntegrity] = useState<unknown>(null)
  const [proposalSummary, setProposalSummary] = useState<unknown>(null)
  const [proposalDetailId, setProposalDetailId] = useState('')
  const [proposalDetail, setProposalDetail] = useState<unknown>(null)
  const [proposalLoading, setProposalLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')

  const isAdminAllowed = !adminEmails.length || (profileEmail ? adminEmails.includes(profileEmail) : false)

  useEffect(() => {
    const token = window.localStorage.getItem('helpus_google_token') || ''
    setGoogleToken(token)
    setProfileEmail(token ? decodeJwtEmail(token) : '')
  }, [])

  const fetchLocal = useCallback(
    async <T,>(path: string): Promise<T> => {
      const response = await fetch(`${apiUrl}${path}`, {
        cache: 'no-store',
        headers: { Authorization: `Bearer ${googleToken}` },
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        const detail = typeof data?.detail === 'string' ? data.detail : `Erro HTTP ${response.status}`
        throw new Error(detail)
      }
      return data as T
    },
    [apiUrl, googleToken],
  )

  const postLocal = useCallback(
    async <T,>(path: string, body: JsonObject): Promise<T> => {
      const response = await fetch(`${apiUrl}${path}`, {
        body: JSON.stringify(body),
        cache: 'no-store',
        headers: {
          Authorization: `Bearer ${googleToken}`,
          'Content-Type': 'application/json',
        },
        method: 'POST',
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        const detail = typeof data?.detail === 'string' ? data.detail : `Erro HTTP ${response.status}`
        throw new Error(detail)
      }
      return data as T
    },
    [apiUrl, googleToken],
  )

  const carregarLocal = useCallback(async () => {
    if (!googleToken) {
      setErro('Token Google ausente. Volte ao painel principal e autentique primeiro.')
      return
    }
    if (!isAdminAllowed) {
      setErro('E-mail autenticado não está autorizado para o painel administrativo.')
      return
    }

    try {
      setLoading(true)
      setErro('')
      const [status, diff, files, search, phaseAPlan, blockedPlan] = await Promise.all([
        fetchLocal<JsonObject>('/local/status'),
        fetchLocal<JsonObject>('/local/diff'),
        fetchLocal<LocalFilesResult>('/local/files/list?path=docs%2F&limit=25'),
        fetchLocal<LocalSearchResult>('/local/docs/search?q=HelpUS%20AI&path=docs%2F&limit=10'),
        postLocal<LocalPlanResult>('/local/plan', { intent: 'phase_a_validation' }),
        postLocal<LocalPlanResult>('/local/plan', { command: 'git push origin main' }),
      ])
      setSnapshot({ status, diff, files, search, phaseAPlan, blockedPlan })
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao carregar diagnóstico local read-only.')
    } finally {
      setLoading(false)
    }
  }, [fetchLocal, googleToken, isAdminAllowed, postLocal])

  const planejarIntent = useCallback(async () => {
    try {
      setPlanning(true)
      setErro('')
      const plan = await postLocal<LocalPlanResult>('/local/plan', { intent: customIntent })
      setCustomPlan(plan)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao planejar intent.')
    } finally {
      setPlanning(false)
    }
  }, [customIntent, postLocal])

  const planejarComando = useCallback(async () => {
    try {
      setPlanning(true)
      setErro('')
      const plan = await postLocal<LocalPlanResult>('/local/plan', { command: customCommand })
      setCustomPlan(plan)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao planejar comando.')
    } finally {
      setPlanning(false)
    }
  }, [customCommand, postLocal])

  useEffect(() => {
    if (googleToken) void carregarLocal()
  }, [carregarLocal, googleToken])


  const criarPropostaAuditavel = useCallback(async () => {
    try {
      setProposalLoading(true)
      setErro('')
      const proposal = await postLocal<unknown>('/local/plan/proposals', {
        intent: customIntent,
        note: proposalNote,
        created_by: 'admin-local-ui',
      })
      setProposalResult(proposal)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao criar proposta auditavel.')
    } finally {
      setProposalLoading(false)
    }
  }, [customIntent, postLocal, proposalNote])

  const carregarPropostasAuditaveis = useCallback(async () => {
    try {
      setProposalLoading(true)
      setErro('')
      const proposalList = await fetchLocal<unknown>('/local/plan/proposals?limit=20')
      setProposals(proposalList)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao listar propostas auditaveis.')
    } finally {
      setProposalLoading(false)
    }
  }, [fetchLocal])

  const verificarIntegridadePropostas = useCallback(async () => {
    try {
      setProposalLoading(true)
      setErro('')
      const integrity = await fetchLocal<unknown>('/local/plan/proposals/verify')
      setProposalIntegrity(integrity)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao verificar integridade das propostas.')
    } finally {
      setProposalLoading(false)
    }
  }, [fetchLocal])

  const carregarResumoPropostas = useCallback(async () => {
    setErro('')
    try {
      const summary = await fetchLocal<unknown>('/local/plan/proposals/summary?limit=200')
      setProposalSummary(summary)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao carregar resumo auditavel.')
    }
  }, [fetchLocal])

  const usarPropostaIdAuditavel = useCallback((source: unknown) => {
    const id = findProposalId(source)
    if (!id) {
      setErro('Nenhum proposal_id encontrado para preencher o detalhe auditavel.')
      return
    }
    setProposalDetailId(id)
    setErro('')
  }, [])

  const carregarDetalheProposta = useCallback(async () => {
    const normalized = proposalDetailId.trim()
    if (!normalized) {
      setErro('Informe um proposal_id para carregar detalhe auditavel.')
      return
    }
    try {
      setProposalLoading(true)
      setErro('')
      const detail = await fetchLocal<unknown>(`/local/plan/proposals/${encodeURIComponent(normalized)}`)
      setProposalDetail(detail)
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Falha ao carregar detalhe auditavel.')
    } finally {
      setProposalLoading(false)
    }
  }, [fetchLocal, proposalDetailId])

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">HelpUSAI Admin</p>
              <h1 className="mt-2 text-3xl font-semibold">Operador local read-only</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
                Painel de diagnóstico seguro para consultar status, diff, listagem de documentos, busca local e planos seguros sem executar ações destrutivas.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800" href="/admin">
                Voltar ao admin
              </Link>
              <button
                className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loading}
                onClick={() => void carregarLocal()}
                type="button"
              >
                {loading ? 'Atualizando...' : 'Atualizar diagnóstico'}
              </button>
            </div>
          </div>
          <div className="mt-5 grid gap-3 text-sm md:grid-cols-3">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <p className="text-slate-400">API</p>
              <p className="mt-1 font-mono text-cyan-200">{apiUrl}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <p className="text-slate-400">Perfil</p>
              <p className="mt-1 font-mono text-cyan-200">{profileEmail || 'não autenticado'}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <p className="text-slate-400">Modo</p>
              <p className="mt-1 font-mono text-emerald-300">read-only + plan-only</p>
            </div>
          </div>
        </header>

        {erro ? <section className="rounded-2xl border border-red-700 bg-red-950/50 p-4 text-sm text-red-100">{erro}</section> : null}

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-xl font-semibold">Git status local</h2>
            <pre className="mt-4 max-h-96 overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-5 text-slate-200">{prettyJson(snapshot.status)}</pre>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-xl font-semibold">Diff local</h2>
            <pre className="mt-4 max-h-96 overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-5 text-slate-200">{prettyJson(snapshot.diff)}</pre>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-xl font-semibold">Planejamento seguro</h2>
            <p className="mt-2 text-sm text-slate-400">Resultado de `POST /local/plan`. Nenhum comando é executado por este painel.</p>
            <div className="mt-4 grid gap-4">
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-100">Plano permitido: phase_a_validation</h3>
                  <RiskBadge plan={snapshot.phaseAPlan} />
                </div>
                <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-200">{prettyJson(snapshot.phaseAPlan)}</pre>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-100">Exemplo bloqueado: git push origin main</h3>
                  <RiskBadge plan={snapshot.blockedPlan} />
                </div>
                <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-200">{prettyJson(snapshot.blockedPlan)}</pre>
              </div>
            </div>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-xl font-semibold">Arquivos em docs/</h2>
            <p className="mt-2 text-sm text-slate-400">Resultado de `/local/files/list?path=docs/`.</p>
            <div className="mt-4 max-h-96 overflow-auto rounded-xl border border-slate-800 bg-slate-950">
              {(snapshot.files?.files || []).map((file) => (
                <div className="border-b border-slate-800 px-4 py-3 last:border-b-0" key={file.path}>
                  <p className="font-mono text-sm text-cyan-200">{file.path}</p>
                  <p className="mt-1 text-xs text-slate-500">{file.size} bytes</p>
                </div>
              ))}
              {snapshot.files && !(snapshot.files.files || []).length ? <p className="p-4 text-sm text-slate-400">Nenhum arquivo retornado.</p> : null}
            </div>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 lg:col-span-2">
            <h2 className="text-xl font-semibold">Planner customizado</h2>
            <p className="mt-2 text-sm text-slate-400">
              Teste intents ou comandos contra o contrato plan-only. Endpoint disponível: /local/plan/intents.
            </p>
            <div className="mt-4 grid gap-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
              <label className="grid gap-2 text-sm">
                <span className="font-semibold text-slate-200">Intent controlada</span>
                <select
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                  onChange={(event) => setCustomIntent(event.target.value)}
                  value={customIntent}
                >
                  <option value="phase_b_validation">phase_b_validation</option>
                  <option value="phase_a_validation">phase_a_validation</option>
                  <option value="local_status">local_status</option>
                  <option value="local_diff">local_diff</option>
                  <option value="local_recent_commits">local_recent_commits</option>
                  <option value="build">build</option>
                </select>
              </label>
              <button
                className="rounded-lg border border-cyan-500 px-4 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-950 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={planning}
                onClick={() => void planejarIntent()}
                type="button"
              >
                Planejar intent sem executar
              </button>
              <label className="grid gap-2 text-sm">
                <span className="font-semibold text-slate-200">Comando para classificar</span>
                <input
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-slate-100"
                  maxLength={240}
                  onChange={(event) => setCustomCommand(event.target.value)}
                  value={customCommand}
                />
              </label>
              <button
                className="rounded-lg border border-amber-500 px-4 py-2 text-sm font-semibold text-amber-100 hover:bg-amber-950 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={planning}
                onClick={() => void planejarComando()}
                type="button"
              >
                Classificar comando sem executar
              </button>
              <div className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-xs text-slate-400">
                Contrato: máximo 5 comandos, 240 caracteres por comando, sem chaining, sem deploy, sem git push/commit/add/reset/clean.
              </div>
              {customPlan ? (
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-semibold text-slate-100">Resultado customizado</h3>
                    <RiskBadge plan={customPlan} />
                  </div>
                  <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-200">{prettyJson(customPlan)}</pre>
                </div>
              ) : null}
            </div>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 lg:col-span-2">
            <h2 className="text-xl font-semibold">Propostas auditaveis</h2>
            <p className="mt-2 text-sm text-slate-400">
              Registra propostas em modo proposal_only para auditoria humana antes de qualquer execucao real.
              Endpoints: POST /local/plan/proposals e GET /local/plan/proposals.
            </p>
            <div className="mt-4 grid gap-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
              <label className="grid gap-2 text-sm">
                <span className="font-semibold text-slate-200">Nota da proposta</span>
                <input
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                  maxLength={180}
                  onChange={(event) => setProposalNote(event.target.value)}
                  value={proposalNote}
                />
              </label>
              <label className="grid gap-2 text-sm">
                <span className="font-semibold text-slate-200">proposal_id para detalhe auditavel</span>
                <input
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-slate-100"
                  maxLength={120}
                  onChange={(event) => setProposalDetailId(event.target.value)}
                  placeholder="Cole o proposal_id"
                  value={proposalDetailId}
                />
              </label>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">proposal_id detectado automaticamente</p>
                <p className="mt-1 font-mono text-cyan-200">
                  {findProposalId(proposalResult) || findProposalId(proposals) || 'Nenhum proposal_id detectado na proposta criada ou na lista.'}
                </p>
                <p className="mt-1 text-slate-400">
                  Hint read-only: use os botões abaixo para preencher o campo; o detalhe só carrega no botão Carregar detalhe auditavel.
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">Status do proposal_id para detalhe</p>
                <p className="mt-1 text-slate-400">
                  {proposalDetailId.trim()
                    ? 'Pronto para consulta GET read-only.'
                    : 'Informe ou preencha um proposal_id antes de carregar o detalhe.'}
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">proposal_id normalizado para detalhe</p>
                <p className="mt-1 font-mono text-cyan-200">
                  {proposalDetailId.trim() || 'Nenhum proposal_id informado.'}
                </p>
                <p className="mt-1 text-slate-400">
                  Valor read-only: derivado do campo manual/de detalhe; nenhuma API e chamada automaticamente.
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">Limite da consulta GET de detalhe</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-slate-400">
                  <li>Status, normalizacao, codificacao, checklist e preview sao somente leitura.</li>
                  <li>A consulta GET de detalhe acontece apenas ao clicar em Carregar detalhe auditavel.</li>
                  <li>Estes blocos nao criam proposta, nao aprovam nada e nao executam comandos.</li>
                </ul>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">Checklist GET detalhe auditavel</p>
                <ol className="mt-2 list-decimal space-y-1 pl-4 text-slate-400">
                  <li>Confirme o proposal_id normalizado.</li>
                  <li>Confira o proposal_id codificado.</li>
                  <li>Revise o Preview GET detalhe auditavel.</li>
                  <li>Clique em Carregar detalhe auditavel somente quando quiser consultar.</li>
                </ol>
                <p className="mt-2 text-slate-400">
                  Checklist read-only: este bloco nao chama API, nao preenche campos e nao executa comandos.
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">proposal_id codificado para endpoint de detalhe</p>
                <p className="mt-1 font-mono text-cyan-200">
                  {proposalDetailId.trim()
                    ? encodeURIComponent(proposalDetailId.trim())
                    : 'Nenhum proposal_id para codificar.'}
                </p>
                <p className="mt-1 text-slate-400">
                  Valor read-only: apenas mostra a codificacao que sera usada no Preview GET detalhe auditavel.
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
                <p className="font-semibold text-slate-200">Preview GET detalhe auditavel</p>
                <p className="mt-1 font-mono text-emerald-200">
                  {proposalDetailId.trim()
                    ? `/local/plan/proposals/${encodeURIComponent(proposalDetailId.trim())}`
                    : '/local/plan/proposals/{proposal_id}'}
                </p>
                <p className="mt-1 text-slate-400">
                  Preview read-only: nao chama API automaticamente; apenas mostra o endpoint que sera usado ao clicar em Carregar detalhe auditavel.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  className="rounded-lg border border-cyan-500 px-4 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-950 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={proposalLoading}
                  onClick={() => void criarPropostaAuditavel()}
                  type="button"
                >
                  Criar proposta auditavel sem executar
                </button>
                <button
                  className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={proposalLoading}
                  onClick={() => void carregarPropostasAuditaveis()}
                  type="button"
                >
                  Listar propostas auditaveis
                </button>
                <button
                  className="rounded-lg border border-indigo-500 px-4 py-2 text-sm font-semibold text-indigo-100 hover:bg-indigo-950 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={proposalLoading || !findProposalId(proposalResult)}
                  onClick={() => usarPropostaIdAuditavel(proposalResult)}
                  type="button"
                >
                  Preencher id da proposta criada
                </button>
                <button
                  className="rounded-lg border border-indigo-500 px-4 py-2 text-sm font-semibold text-indigo-100 hover:bg-indigo-950 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={proposalLoading || !findProposalId(proposals)}
                  onClick={() => usarPropostaIdAuditavel(proposals)}
                  type="button"
                >
                  Preencher id da lista
                </button>
                <button
                  className="rounded-lg border border-sky-500 px-4 py-2 text-sm font-semibold text-sky-100 hover:bg-sky-950 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={proposalLoading || !proposalDetailId.trim()}
                  onClick={() => void carregarDetalheProposta()}
                  type="button"
                >
                  Carregar detalhe auditavel
                </button>
                <button
                  type="button"
                  onClick={() => void carregarResumoPropostas()}
                  className="rounded-md border px-3 py-2 text-sm font-medium"
                >
                  Carregar resumo auditavel
                </button>
                <button
                  className="rounded-lg border border-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-100 hover:bg-emerald-950 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={proposalLoading}
                  onClick={() => void verificarIntegridadePropostas()}
                  type="button"
                >
                  Verificar integridade auditavel
                </button>
              </div>
              <p className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-xs text-slate-400">
                proposal_only: executed=false, approved=false, approval_status=pending_human_review.
              </p>
              <div>
                <h3 className="font-semibold text-slate-100">Resultado da integridade</h3>
                <pre className="mt-2 max-h-64 overflow-auto rounded-xl border border-emerald-900 bg-slate-950 p-4 text-xs text-emerald-100">
                  {proposalIntegrity ? prettyJson(proposalIntegrity) : 'Clique em Verificar integridade auditavel para consultar /local/plan/proposals/verify.'}
                </pre>
              </div>
              <div>
                <h3 className="font-semibold text-slate-100">Resultado da proposta</h3>
                <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-200">{prettyJson(proposalResult)}</pre>
              </div>
              {proposalSummary ? (
                <div>
                  <h3 className="text-lg font-semibold">Resumo auditavel</h3>
                  <pre className="mt-2 max-h-64 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-200">
                    {JSON.stringify(proposalSummary, null, 2)}
                  </pre>
                </div>
              ) : null}
              <div>
                <h3 className="font-semibold text-slate-100">Lista de propostas</h3>
                <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-200">{prettyJson(proposals)}</pre>
              </div>
              <div>
                <h3 className="font-semibold text-slate-100">Detalhe da proposta</h3>
                <p className="mt-1 text-xs text-slate-400">{'GET /local/plan/proposals/{proposal_id}'}</p>
                <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-slate-900 p-3 text-xs leading-5 text-slate-200">
                  {proposalDetail ? prettyJson(proposalDetail) : 'Informe proposal_id e clique em Carregar detalhe auditavel.'}
                </pre>
              </div>
            </div>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 lg:col-span-2">
            <h2 className="text-xl font-semibold">Busca em docs/</h2>
            <p className="mt-2 text-sm text-slate-400">Resultado de `/local/docs/search?q=HelpUS AI`.</p>
            <div className="mt-4 max-h-96 overflow-auto rounded-xl border border-slate-800 bg-slate-950">
              {(snapshot.search?.matches || []).map((match) => (
                <div className="border-b border-slate-800 px-4 py-3 last:border-b-0" key={`${match.path}:${match.line}:${match.text}`}>
                  <p className="font-mono text-sm text-cyan-200">{match.path}:{match.line}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{match.text}</p>
                </div>
              ))}
              {snapshot.search && !(snapshot.search.matches || []).length ? <p className="p-4 text-sm text-slate-400">Nenhum resultado retornado.</p> : null}
            </div>
          </article>
        </section>
      </div>
    </main>
  )
}
