import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'HelpUS',
  description: 'HelpUS - Seu Assistente Inteligente',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
