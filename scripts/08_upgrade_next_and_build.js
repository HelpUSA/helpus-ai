const cp = require("child_process");
const path = require("path");

const frontend = path.join("D:/dev/ai", "frontend");

function run(cmd, args) {
  console.log(`\n[run] ${cmd} ${args.join(" ")}`);
  cp.execFileSync(cmd, args, {
    cwd: frontend,
    stdio: "inherit",
    shell: true,
  });
}

run("npm", ["install", "next@latest", "react@latest", "react-dom@latest"]);
run("npm", ["run", "build"]);
run("npm", ["audit", "--audit-level=moderate"]);

console.log("\n[next] Upgrade/build/audit completed.");
