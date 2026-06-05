const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const page = path.join(root, "frontend/src/app/page.tsx");

let src = fs.readFileSync(page, "utf8");

src = src.replace(
  "      if (sessionId === id) {\n        setMessages([])\n        setSessionId('')\n      }\n      await carregarConversas()",
  "      if (sessionId === id) {\n        setMessages([])\n        setSessionId('')\n      }\n      await carregarConversas()\n      setSidebarOpen(false)"
);

src = src.replace(
  "  const limparChat = () => {\n    setMessages([])\n    setSessionId('')\n    setInput('')\n  }",
  "  const limparChat = () => {\n    setMessages([])\n    setSessionId('')\n    setInput('')\n    setSidebarOpen(false)\n  }"
);

src = src.replace(
  "            <div className=\"mb-3 flex items-center justify-between\">\n              <h2 className=\"font-bold text-slate-800\">Minhas conversas</h2>\n              <button\n                onClick={() => carregarConversas()}\n                disabled={!profile || historyLoading}\n                className=\"rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 disabled:opacity-50\"\n              >\n                Atualizar\n              </button>\n            </div>",
  "            <div className=\"mb-3 flex items-center justify-between gap-2\">\n              <h2 className=\"font-bold text-slate-800\">Minhas conversas</h2>\n              <div className=\"flex items-center gap-2\">\n                <button\n                  onClick={() => setSidebarOpen(false)}\n                  className=\"rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 lg:hidden\"\n                >\n                  Voltar ao chat\n                </button>\n                <button\n                  onClick={() => carregarConversas()}\n                  disabled={!profile || historyLoading}\n                  className=\"rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 disabled:opacity-50\"\n                >\n                  Atualizar\n                </button>\n              </div>\n            </div>\n\n            <button\n              onClick={limparChat}\n              className=\"mb-3 w-full rounded-xl border border-blue-100 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-100\"\n            >\n              Nova conversa\n            </button>"
);

fs.writeFileSync(page, src, "utf8");

console.log("[history-ui] Fixed mobile history navigation");

cp.execFileSync("npm run build", {
  cwd: root,
  stdio: "inherit",
  shell: true,
});

console.log("[history-ui] Build OK");
