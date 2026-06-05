const fs = require("fs");
const path = require("path");

const root = "D:/dev/ai";
const pagePath = path.join(root, "frontend/src/app/page.tsx");
const envPath = path.join(root, "frontend/.env.example");

let src = fs.readFileSync(pagePath, "utf8");
const lines = src.split(/\r?\n/);

const startIndex = lines.findIndex(line => line.includes("const data = await response.json()"));
const catchIndex = lines.findIndex((line, index) => index > startIndex && line.includes("} catch (error) {"));
const finallyIndex = lines.findIndex((line, index) => index > catchIndex && line.includes("} finally {"));

if (startIndex < 0 || catchIndex < 0 || finallyIndex < 0) {
  console.log("startIndex=", startIndex, "catchIndex=", catchIndex, "finallyIndex=", finallyIndex);
  throw new Error("Não foi possível localizar o trecho de enviarMensagem.");
}

const replacement = [
"      const data = await response.json().catch(() => ({}))",
"",
"      if (!response.ok) {",
"        const detail = data?.detail || `Erro HTTP ${response.status}`",
"        throw new Error(String(detail))",
"      }",
"",
"      if (data.session_id && !sessionId) {",
"        setSessionId(data.session_id)",
"      }",
"",
"      setMessages(prev => [",
"        ...prev,",
"        {",
"          role: 'assistant',",
"          content: data.resposta || 'A API respondeu sem conteúdo.',",
"          fontes: data.fontes || [],",
"        },",
"      ])",
"    } catch (error) {",
"      const message = error instanceof Error ? error.message : 'Erro desconhecido'",
"      setMessages(prev => [",
"        ...prev,",
"        {",
"          role: 'assistant',",
"          content: `Erro ao conectar com o servidor: ${message}`,",
"        },",
"      ])"
];

const newLines = [
  ...lines.slice(0, startIndex),
  ...replacement,
  ...lines.slice(finallyIndex)
];

fs.writeFileSync(pagePath, newLines.join("\n"), "utf8");
fs.writeFileSync(envPath, "NEXT_PUBLIC_API_URL=http://localhost:8000\n", "utf8");

console.log("[frontend] Patched page.tsx");
console.log("[frontend] Wrote .env.example");
