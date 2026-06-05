const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";
const frontend = path.join(root, "frontend");
const page = path.join(frontend, "src/app/page.tsx");

let src = fs.readFileSync(page, "utf8");

src = src.replace(
  "const [pesquisarWeb, setPesquisarWeb] = useState(true)",
  "const [pesquisarWeb, setPesquisarWeb] = useState(false)"
);

src = src.replace(
  "Pesquisar na web",
  "Pesquisar na web quando necessario"
);

fs.writeFileSync(page, src, "utf8");

console.log("[frontend] Default web search disabled");

cp.execFileSync("npm run build", {
  cwd: root,
  stdio: "inherit",
  shell: true
});
