const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const frontend = path.join(root, "frontend");
const layoutPath = path.join(frontend, "src/app/layout.tsx");

const layout = `import type { Metadata } from 'next'
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
`;

fs.writeFileSync(layoutPath, layout, "utf8");
console.log("[frontend] Rewrote layout.tsx as clean UTF-8");

console.log("[frontend] Running npm build...");
cp.execFileSync("npm", ["run", "build"], {
  cwd: frontend,
  stdio: "inherit",
  shell: true,
});
