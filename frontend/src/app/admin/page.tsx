'use client'
import Link from 'next/link'

export default function AdminPage() {
  return (
    <main className="min-h-screen bg-[#212121] px-4 py-6 text-zinc-100">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-3xl flex-col justify-center">
        <div className="rounded-3xl border border-white/10 bg-zinc-950/60 p-8 shadow-2xl shadow-black/30">
          <div className="mb-8">
            <p className="mb-3 text-sm font-medium text-zinc-400">HelpUS</p>
            <h1 className="text-3xl font-semibold tracking-tight text-white">Area interna em preparacao</h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-zinc-400">
              Esta pagina deixou de ser um painel tecnico publico. O chat principal continua sendo o centro da experiencia HelpUS.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p4">
              <h2 className="font-medium text-zinc-100">Painel operacional</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                Em breve, esta area podera concentrar metricas, configuracoes e monitoramento real.
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p4">
              <h2 className="font-medium text-zinc-100">Acesso controlado</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                Informacoes tecnicas e endpoints nao ficam mais expostos para o usuario comum.
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-full bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200"
            >
              Voltar ao chat
            </Link>
            <span className="inline-flex items-center justify-center rounded-full border border-white/10 px-5 py-3 text-sm text-zinc-400">
              Admin completo em breve
            </span>
          </div>
        </div>
      </div>
    </main>
  )
}
