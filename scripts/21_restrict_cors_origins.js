const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const backend = path.join(root, "backend");
const configPath = path.join(backend, "config.py");
const mainPath = path.join(backend, "main.py");

let config = fs.readFileSync(configPath, "utf8");

if (!config.includes("CORS_ORIGINS")) {
  config += `

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://ai.helpusbr.com,https://helpus-ai.vercel.app,http://localhost:3000"
    ).split(",")
    if origin.strip()
]
`;
}

fs.writeFileSync(configPath, config, "utf8");

let main = fs.readFileSync(mainPath, "utf8");

if (!main.includes("CORS_ORIGINS")) {
  main = main.replace(
    "from config import",
    "from config import"
  );

  const importPattern = /from config import \(([\s\S]*?)\)/m;
  if (importPattern.test(main)) {
    main = main.replace(importPattern, (match, inner) => {
      if (inner.includes("CORS_ORIGINS")) return match;
      return `from config import (${inner.trimEnd()},\n    CORS_ORIGINS,\n)`;
    });
  } else {
    main = main.replace(
      /from config import ([^\n]+)/,
      (match, names) => {
        if (names.includes("CORS_ORIGINS")) return match;
        return `from config import ${names}, CORS_ORIGINS`;
      }
    );
  }
}

main = main.replace(
  /allow_origins\s*=\s*\[\s*["']\*["']\s*\]/,
  "allow_origins=CORS_ORIGINS"
);

fs.writeFileSync(mainPath, main, "utf8");

console.log("[cors] Updated config.py and main.py");

cp.execFileSync("python -m py_compile config.py banco.py cerebro.py buscador.py main.py", {
  cwd: backend,
  stdio: "inherit",
  shell: true,
});

console.log("[cors] Backend compile OK");
