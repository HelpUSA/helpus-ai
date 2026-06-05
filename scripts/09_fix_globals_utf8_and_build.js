const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const frontend = path.join(root, "frontend");
const globalsPath = path.join(frontend, "src/app/globals.css");

const css = `@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 17, 24, 39;
  --background-rgb: 243, 244, 246;
}

* {
  box-sizing: border-box;
}

html,
body {
  max-width: 100vw;
  min-height: 100vh;
  overflow-x: hidden;
}

body {
  color: rgb(var(--foreground-rgb));
  background: rgb(var(--background-rgb));
}

a {
  color: inherit;
  text-decoration: none;
}

textarea,
button,
input {
  font: inherit;
}
`;

fs.writeFileSync(globalsPath, css, "utf8");
console.log("[frontend] Rewrote globals.css as clean UTF-8");

console.log("[frontend] Running npm build...");
cp.execFileSync("npm", ["run", "build"], {
  cwd: frontend,
  stdio: "inherit",
  shell: true,
});

console.log("[frontend] Running npm audit --audit-level=moderate...");
const audit = cp.spawnSync("npm", ["audit", "--audit-level=moderate"], {
  cwd: frontend,
  stdio: "inherit",
  shell: true,
});

if (audit.status !== 0) {
  console.log("[frontend] Audit reported vulnerabilities. Build passed; audit is recorded but not blocking.");
}

console.log("[frontend] Build completed.");
