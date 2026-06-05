const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const backend = path.join(root, "backend");
const file = path.join(backend, "cerebro.py");

let src = fs.readFileSync(file, "utf8");

const oldText = "partes = ['Você é o HelpUS, um assistente virtual profissional em português do Brasil.', 'Responda de forma clara, amigável e objetiva.']";

const newText = `partes = [
            'Você é o HelpUS, um assistente virtual profissional em português do Brasil.',
            'Seu nome público é HelpUS.',
            'Nunca diga que você é Gemini, Google, OpenAI, ChatGPT ou outro provedor.',
            'Quando perguntarem quem você é, responda que é o HelpUS, o assistente inteligente da HelpUS.',
            'Você pode usar IA generativa para responder, mas não deve se apresentar como o modelo base.',
            'Responda de forma clara, amigável e objetiva.'
        ]`;

if (!src.includes(oldText)) {
  throw new Error("Trecho de identidade não encontrado em backend/cerebro.py");
}

src = src.replace(oldText, newText);

fs.writeFileSync(file, src, "utf8");

console.log("[identity] Updated HelpUS identity prompt");

console.log("[identity] Running backend compile check...");
cp.execFileSync("python -m py_compile config.py banco.py cerebro.py buscador.py main.py", {
  cwd: backend,
  stdio: "inherit",
  shell: true
});

console.log("[identity] Done.");
