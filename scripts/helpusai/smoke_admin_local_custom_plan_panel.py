from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "admin" / "local" / "page.tsx"
text = PAGE.read_text(encoding="utf-8")
required_markers = [
    "/local/plan/intents",
    "Planner customizado",
    "Planejar intent sem executar",
    "Classificar comando sem executar",
    "Resultado customizado",
    "Contrato: máximo 5 comandos, 240 caracteres por comando",
    "phase_b_validation",
    "setCustomPlan(plan)",
]
missing = [marker for marker in required_markers if marker not in text]
if missing:
    raise SystemExit(f"missing markers: {missing}")
print("OK smoke_admin_local_custom_plan_panel")
