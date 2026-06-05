const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";

const config = {
  experimentalServices: {
    frontend: {
      root: "frontend",
      routePrefix: "/",
      framework: "nextjs"
    }
  }
};

fs.writeFileSync(
  path.join(root, "vercel.json"),
  JSON.stringify(config, null, 2) + "\n",
  "utf8"
);

console.log("[vercel] Wrote frontend-only vercel.json");
console.log("[vercel] Testing root build...");

cp.execFileSync("npm run build", {
  cwd: root,
  stdio: "inherit",
  shell: true
});

console.log("[vercel] OK");
