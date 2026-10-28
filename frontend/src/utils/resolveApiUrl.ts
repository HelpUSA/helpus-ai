/**
 * Utilitário de Resolução Resiliente de URL de API
 * 
 * Evita dependência exclusiva de provedores externos ou regras de substring pontuais.
 * Prioriza rotas relativas co-localizadas na Vercel quando:
 * - A variável de ambiente não estiver definida ou for vazia ('')
 * - For solicitado uso local forçado (NEXT_PUBLIC_FORCE_LOCAL_API === 'true')
 * - A URL apontar para hosts externos conhecidos por desativação ou indisponibilidade
 * - A URL tiver formato malformado ou coincidir com a própria origem do navegador
 */

export interface ApiResolutionOptions {
  rawUrl?: string
  forceLocal?: boolean
  currentOrigin?: string
}

export function resolveApiUrl(options: ApiResolutionOptions = {}): string {
  const {
    rawUrl = (typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_API_URL : '') || '',
    forceLocal = (typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_FORCE_LOCAL_API === 'true' : false),
    currentOrigin = (typeof window !== 'undefined' && window.location?.origin) ? window.location.origin : '',
  } = options

  if (forceLocal) {
    return ''
  }

  const trimmed = rawUrl.trim()
  if (!trimmed || trimmed === '/' || trimmed.toLowerCase() === 'auto' || trimmed.toLowerCase() === 'local') {
    return ''
  }

  // Se já for uma rota relativa válida (ex: /api)
  if (trimmed.startsWith('/') && !trimmed.startsWith('//')) {
    return trimmed
  }

  try {
    const parsed = new URL(trimmed)

    // Se no navegador a URL coincidir exatamente com a origem atual, usa rota relativa limpa
    if (currentOrigin && parsed.origin === currentOrigin) {
      return ''
    }

    // Lista de domínios descontinuados ou com indisponibilidade crônica conhecida
    const deprecatedDomains = ['railway.app', 'up.railway.app', 'herokuapp.com']
    if (deprecatedDomains.some(d => parsed.hostname === d || parsed.hostname.endsWith(`.${d}`))) {
      return ''
    }

    return trimmed.replace(/\/+$/, '')
  } catch {
    // Fail-safe: se a URL for inválida, utiliza rota co-localizada
    return ''
  }
}
