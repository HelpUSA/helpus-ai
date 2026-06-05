const fs = require("fs");
const path = require("path");

const pagePath = path.join("D:/dev/ai", "frontend/src/app/page.tsx");
let src = fs.readFileSync(pagePath, "utf8");

src = src.replace('            <p className="text-4xl mb-4"></p>\n', '');
src = src.replace('                     Fontes consultadas:', '                    Fontes consultadas:');

fs.writeFileSync(pagePath, src, "utf8");
console.log("[frontend] Polished text spacing");
