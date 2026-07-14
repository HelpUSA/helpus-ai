
'use client'

import {
  isValidElement,
  useState,
  type ReactNode,
} from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export type MessageSource = {
  titulo: string
  url: string
  fonte: string
}

type CodeElementProperties = {
  children?: ReactNode
  className?: string
}

export function normalizeHttpUrl(
  value?: string,
) {
  const candidate =
    (value || '').trim()

  if (!candidate) {
    return ''
  }

  try {
    const parsed =
      new URL(candidate)

    if (
      parsed.protocol !== 'http:'
      && parsed.protocol !== 'https:'
    ) {
      return ''
    }

    return parsed.toString()
  } catch {
    return ''
  }
}

function sourceHostname(
  value: string,
) {
  try {
    return new URL(value).hostname
  } catch {
    return ''
  }
}

function nodeText(
  value: ReactNode,
): string {
  if (
    typeof value === 'string'
    || typeof value === 'number'
  ) {
    return String(value)
  }

  if (Array.isArray(value)) {
    return value
      .map(nodeText)
      .join('')
  }

  if (
    isValidElement<{
      children?: ReactNode
    }>(value)
  ) {
    return nodeText(
      value.props.children,
    )
  }

  return ''
}

export function SafeSourceLink({
  fonte,
  index,
}: {
  fonte: MessageSource
  index: number
}) {
  const safeUrl =
    normalizeHttpUrl(fonte.url)

  if (!safeUrl) {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-amber-400/15 bg-amber-400/[0.05] px-3 py-2.5">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-300/10 text-[11px] font-semibold text-amber-100">
          {index + 1}
        </span>

        <span className="min-w-0">
          <span className="block truncate text-sm font-medium text-zinc-300">
            {fonte.titulo}
          </span>

          <span className="mt-0.5 block text-xs text-amber-100/60">
            Link bloqueado por protocolo não permitido
          </span>
        </span>
      </div>
    )
  }

  const hostname =
    sourceHostname(safeUrl)

  return (
    <a
      href={safeUrl}
      target="_blank"
      rel="noopener noreferrer nofollow"
      title={safeUrl}
      className="group flex items-start gap-3 rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 transition hover:border-white/20 hover:bg-white/[0.06]"
    >
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/[0.06] text-[11px] font-semibold text-zinc-300 transition group-hover:bg-white/10 group-hover:text-white">
        {index + 1}
      </span>

      <span className="min-w-0">
        <span className="block truncate text-sm font-medium text-zinc-200 group-hover:text-white">
          {fonte.titulo}
        </span>

        <span className="mt-0.5 block truncate text-xs text-zinc-500 group-hover:text-zinc-400">
          {fonte.fonte}
          {hostname
            ? ` · ${hostname}`
            : ''}
        </span>
      </span>

      <span
        className="ml-auto shrink-0 text-xs text-zinc-600 transition group-hover:text-zinc-300"
        aria-hidden="true"
      >
        ↗
      </span>
    </a>
  )
}

export function MarkdownMessage({
  content,
}: {
  content: string
}) {
  const [
    copiedCode,
    setCopiedCode,
  ] = useState<string | null>(null)

  const [
    copyNotice,
    setCopyNotice,
  ] = useState('')

  const copyCodeBlock =
    async (
      value: string,
    ) => {
      if (!value) {
        return
      }

      try {
        if (!navigator.clipboard) {
          throw new Error(
            'Clipboard indisponível',
          )
        }

        await navigator.clipboard.writeText(
          value,
        )

        setCopiedCode(value)
        setCopyNotice('')

        window.setTimeout(
          () => {
            setCopiedCode(
              (current) =>
                current === value
                  ? null
                  : current,
            )
          },
          1800,
        )
      } catch {
        setCopyNotice(
          'Não foi possível copiar o bloco de código.',
        )

        window.setTimeout(
          () => setCopyNotice(''),
          2600,
        )
      }
    }

  return (
    <div className="markdown-message text-[15px] leading-7 text-inherit sm:text-base">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        urlTransform={normalizeHttpUrl}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-3 mt-6 text-2xl font-semibold tracking-tight text-zinc-50 first:mt-0">
              {children}
            </h1>
          ),

          h2: ({ children }) => (
            <h2 className="mb-3 mt-6 text-xl font-semibold tracking-tight text-zinc-50 first:mt-0">
              {children}
            </h2>
          ),

          h3: ({ children }) => (
            <h3 className="mb-2 mt-5 text-lg font-semibold text-zinc-100 first:mt-0">
              {children}
            </h3>
          ),

          p: ({ children }) => (
            <p className="my-3 whitespace-pre-wrap first:mt-0 last:mb-0">
              {children}
            </p>
          ),

          ul: ({ children }) => (
            <ul className="my-3 list-disc space-y-1.5 pl-6 marker:text-zinc-500">
              {children}
            </ul>
          ),

          ol: ({ children }) => (
            <ol className="my-3 list-decimal space-y-1.5 pl-6 marker:text-zinc-500">
              {children}
            </ol>
          ),

          li: ({ children }) => (
            <li className="pl-1">
              {children}
            </li>
          ),

          blockquote: ({ children }) => (
            <blockquote className="my-4 border-l-4 border-sky-400/30 bg-sky-400/[0.05] px-4 py-2 text-zinc-300">
              {children}
            </blockquote>
          ),

          a: ({
            href,
            children,
            title,
          }) => {
            const safeUrl =
              normalizeHttpUrl(href)

            if (!safeUrl) {
              return (
                <span
                  className="text-amber-200 underline decoration-amber-300/30 underline-offset-2"
                  title="Link bloqueado por protocolo não permitido"
                >
                  {children}
                </span>
              )
            }

            return (
              <a
                href={safeUrl}
                target="_blank"
                rel="noopener noreferrer nofollow"
                title={title || safeUrl}
                className="font-medium text-sky-300 underline decoration-sky-300/30 underline-offset-2 transition hover:text-sky-200 hover:decoration-sky-200"
              >
                {children}
              </a>
            )
          },

          pre: ({ children }) => {
            const codeElement =
              isValidElement<CodeElementProperties>(
                children,
              )
                ? children
                : null

            const codeText =
              nodeText(
                codeElement
                  ? codeElement.props.children
                  : children,
              ).replace(/\n$/, '')

            const language =
              codeElement
                ?.props
                .className
                ?.match(
                  /language-([\w-]+)/,
                )
                ?.[1]
              || 'código'

            const copied =
              Boolean(codeText)
              && copiedCode === codeText

            return (
              <div className="group/code my-4 overflow-hidden rounded-2xl border border-white/10 bg-zinc-950 shadow-inner shadow-black/30">
                <div className="flex items-center justify-between gap-3 border-b border-white/10 bg-white/[0.03] px-4 py-2">
                  <span className="truncate text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                    {language}
                  </span>

                  <button
                    type="button"
                    disabled={!codeText}
                    onClick={() =>
                      void copyCodeBlock(
                        codeText,
                      )}
                    className="rounded-lg border border-white/10 px-2.5 py-1 text-[11px] font-medium text-zinc-400 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {copied
                      ? 'Copiado'
                      : 'Copiar código'}
                  </button>
                </div>

                <pre className="overflow-x-auto p-4 text-sm leading-6 text-zinc-100">
                  {children}
                </pre>
              </div>
            )
          },

          code: ({
            className,
            children,
          }) => {
            const value =
              nodeText(children)

            const blockLike =
              Boolean(className)
              || value.includes('\n')

            if (blockLike) {
              return (
                <code
                  className={`block min-w-max whitespace-pre font-mono text-[13px] text-zinc-100 ${className || ''}`}
                >
                  {children}
                </code>
              )
            }

            return (
              <code className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[13px] text-zinc-100">
                {children}
              </code>
            )
          },

          table: ({ children }) => (
            <div className="my-4 overflow-x-auto rounded-xl border border-white/10">
              <table className="min-w-full border-collapse text-left text-sm">
                {children}
              </table>
            </div>
          ),

          thead: ({ children }) => (
            <thead className="bg-white/[0.06] text-zinc-200">
              {children}
            </thead>
          ),

          tbody: ({ children }) => (
            <tbody className="divide-y divide-white/10">
              {children}
            </tbody>
          ),

          tr: ({ children }) => (
            <tr className="divide-x divide-white/10">
              {children}
            </tr>
          ),

          th: ({ children }) => (
            <th className="px-3 py-2 font-semibold">
              {children}
            </th>
          ),

          td: ({ children }) => (
            <td className="px-3 py-2 align-top text-zinc-300">
              {children}
            </td>
          ),

          hr: () => (
            <hr className="my-6 border-white/10" />
          ),

          del: ({ children }) => (
            <del className="text-zinc-500 decoration-zinc-500">
              {children}
            </del>
          ),

          img: ({
            src,
            alt,
          }) => {
            const safeUrl =
              normalizeHttpUrl(
                typeof src === 'string'
                  ? src
                  : '',
              )

            if (!safeUrl) {
              return (
                <span className="text-amber-200">
                  [Imagem bloqueada]
                </span>
              )
            }

            return (
              <a
                href={safeUrl}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="text-sky-300 underline decoration-sky-300/30 underline-offset-2"
              >
                {alt
                  ? `Imagem: ${alt}`
                  : 'Abrir imagem externa'}
              </a>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>

      {copyNotice ? (
        <p
          className="mt-2 text-xs text-amber-200"
          role="status"
          aria-live="polite"
        >
          {copyNotice}
        </p>
      ) : null}
    </div>
  )
}
