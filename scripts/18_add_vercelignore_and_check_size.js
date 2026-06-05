const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";

const ignore = `# Local heavy archives
_archive_local_not_git/
reports/

# Python local
backend/.venv/
backend/venv/
backend/__pycache__/
**/__pycache__/

# AI models
backend/modelos/
*.gguf
*.bin
*.safetensors
*.pt
*.pth

# Node / Next local
frontend/node_modules/
frontend/.next/
node_modules/
.next/

# Vercel local
.vercel/

# Env files
.env
.env.local
backend/.env
frontend/.env
frontend/.env.local

# Logs
*.log
`;

fs.writeFileSync(path.join(root, ".vercelignore"), ignore, "utf8");
console.log("[vercel] Wrote .vercelignore");

console.log("\n[large files/folders]");
cp.execFileSync(
  "powershell -NoProfile -Command \"Get-ChildItem -LiteralPath D:/dev/ai -Force | Select-Object Mode,Length,Name | Format-Table -AutoSize\"",
  { stdio: "inherit", shell: true }
);

console.log("\n[git status]");
cp.execFileSync("git -C D:/dev/ai status -sb", { stdio: "inherit", shell: true });
