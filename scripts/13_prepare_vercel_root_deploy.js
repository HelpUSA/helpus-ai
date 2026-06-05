const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content.replace(/\r\n/g, "\n"), "utf8");
  console.log("[write]", file);
}

write(path.join(root, "package.json"), `{
  "name": "helpus-ai",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "install:frontend": "npm --prefix frontend install",
    "build": "npm --prefix frontend run build",
    "dev": "npm --prefix frontend run dev",
    "start": "npm --prefix frontend run start"
  }
}
`);

write(path.join(root, "vercel.json"), `{
  "version": 2,
  "installCommand": "npm --prefix frontend install",
  "buildCommand": "npm --prefix frontend run build",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs"
}
`);

console.log("[vercel] Testing root build command...");
cp.execFileSync("npm run build", {
  cwd: root,
  stdio: "inherit",
  shell: true
});

console.log("[vercel] Root deploy config ready.");
