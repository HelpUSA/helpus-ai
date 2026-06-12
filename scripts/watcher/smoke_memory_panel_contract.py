from pathlib import Path

page = Path("frontend/src/app/page.tsx")
text = page.read_text(encoding="utf-8")

required_markers = [
    "interface ProjectMemory",
    "projectMemories",
    "setProjectMemories",
    "carregarMemorias",
    "/memorias",
    "memoryForm",
    "memoryFormOpen",
    "activeProjectId",
    "include_disabled=true",
]

missing = [marker for marker in required_markers if marker not in text]
if missing:
    raise AssertionError(f"Missing memory panel markers: {missing}")

print("MEMORY_PANEL_CONTRACT_SMOKE_OK")
