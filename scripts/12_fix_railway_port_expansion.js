const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = "D:/dev/ai";

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content.replace(/\r\n/g, "\n"), "utf8");
  console.log("[write]", file);
}

const dockerLines = [
  "FROM python:3.14-slim",
  "",
  "WORKDIR /app",
  "",
  "RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*",
  "",
  "COPY backend/requirements.txt ./requirements.txt",
  "RUN pip install --no-cache-dir -r requirements.txt",
  "",
  "COPY backend/ ./",
  "",
  "EXPOSE 8000",
  "",
  "CMD [\"sh\", \"-c\", \"uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\"]",
  ""
];

write(path.join(root, "Dockerfile.railway"), dockerLines.join("\n"));

write(path.join(root, "railway.json"), `{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.railway"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
`);

cp.execFileSync("git -C D:/dev/ai diff --stat", { stdio: "inherit", shell: true });
