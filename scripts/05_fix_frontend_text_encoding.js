const fs = require("fs");
const path = require("path");

const root = "D:/dev/ai";
const pagePath = path.join(root, "frontend/src/app/page.tsx");

let src = fs.readFileSync(pagePath, "utf8");

const replacements = [
  ["{/* �rea de mensagens */}", "{/* Area de mensagens */}"],
  ["Olá! Como posso ajudar?", "Ola! Como posso ajudar?"],
  ["Ol�! Como posso ajudar?", "Ola! Como posso ajudar?"],
  ["Digite sua pergunta abaixo para começar.", "Digite sua pergunta abaixo para comecar."],
  ["Digite sua pergunta abaixo para come�ar.", "Digite sua pergunta abaixo para comecar."],
  ["?? Você", "Voce"],
  ["?? Voc�", "Voce"],
  ["?? Assistente", "Assistente"],
  ["Sessão:", "Sessao:"],
  ["Sess�o:", "Sessao:"],
  ["?? HelpUS", "HelpUS"],
  ["?? Pesquisar na web", "Pesquisar na web"],
  ["??? Nova conversa", "Nova conversa"],
  ["??", ""],
  ["?? Fontes consultadas:", "Fontes consultadas:"],
];

for (const [from, to] of replacements) {
  src = src.split(from).join(to);
}

fs.writeFileSync(pagePath, src, "utf8");
console.log("[frontend] Cleaned mojibake/simple icons in page.tsx");
