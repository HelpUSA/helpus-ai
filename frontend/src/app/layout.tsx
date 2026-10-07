import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'HelpUS - Seu Assistente de IA',
  description: 'Conheça o HelpUS, seu assistente pessoal de inteligência artificial.',
  icons: {
    icon: '/logo-helpus.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className="dark">
      <body className="bg-[#131314] text-[#e3e3e3] antialiased select-auto min-h-screen">
        {children}
      </body>
    </html>
  )
}
