import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'HelpUS',
  description: 'HelpUS Independente - 100% próprio',
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

