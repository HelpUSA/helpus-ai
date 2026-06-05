param(
  [string]$ProjectRoot = "D:/dev/ai",
  [switch]$Apply
)

$ErrorActionPreference = "Stop"

function Say($msg) {
  Write-Output "[prepare] $msg"
}

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archive = Join-Path $root "_archive_local_not_git"
$reportDir = Join-Path $root "reports"
$report = Join-Path $reportDir "cloud_migration_audit_$timestamp.txt"

New-Item -ItemType Directory -Force -Path $archive | Out-Null
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null

Say "Project root: $root"
Say "Apply mode: $Apply"
Say "Report: $report"

"HELPUS CLOUD MIGRATION AUDIT - $timestamp" | Out-File -FilePath $report -Encoding utf8
"ROOT=$root" | Out-File -FilePath $report -Append -Encoding utf8
"" | Out-File -FilePath $report -Append -Encoding utf8

Say "Listing large files..."
Get-ChildItem -LiteralPath $root -Recurse -Force -File |
  Sort-Object Length -Descending |
  Select-Object -First 80 FullName, Length, LastWriteTime |
  Format-Table -AutoSize |
  Out-String -Width 260 |
  Out-File -FilePath $report -Append -Encoding utf8

$itemsToMove = @(
  "backend/venv",
  "backend/__pycache__",
  "frontend/node_modules",
  "frontend/.next",
  "backend/modelos"
)

foreach ($rel in $itemsToMove) {
  $src = Join-Path $root $rel
  if (Test-Path -LiteralPath $src) {
    $safeName = $rel.Replace("/", "__").Replace("\", "__")
    $dst = Join-Path $archive "$safeName`_$timestamp"
    Say "Found: $rel"
    if ($Apply) {
      Say "Moving $src -> $dst"
      Move-Item -LiteralPath $src -Destination $dst
    } else {
      Say "DRY-RUN would move $src -> $dst"
    }
  }
}

$gitignore = Join-Path $root ".gitignore"
$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*.egg-info/
.env
venv/
.venv/

# Local archives / heavy models
_archive_local_not_git/
reports/
backend/modelos/
*.gguf
*.bin
*.safetensors
*.pt
*.pth

# Node / Next
node_modules/
.next/
out/
dist/
.vercel/

# OS / IDE
.vscode/
.idea/
.DS_Store
Thumbs.db

# Logs
*.log
"@

Say "Updating .gitignore"
if ($Apply) {
  Set-Content -LiteralPath $gitignore -Value $gitignoreContent -Encoding utf8
} else {
  Say "DRY-RUN would update .gitignore"
}

if (-not (Test-Path -LiteralPath (Join-Path $root ".git"))) {
  Say "Git repo not found"
  if ($Apply) {
    git -C $root init
  } else {
    Say "DRY-RUN would run git init"
  }
}

Say "Done. Review report: $report"
