import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
"""Static verification checks for UI/UX Modernization invariants in HelpUS AI frontend.

Runs in offline mode without requiring a browser or database.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class UIUXInvariantsTests(unittest.TestCase):
    def setUp(self):
        self.page_source = (ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")

    def test_sidebar_standard_width_and_backdrop(self):
        self.assertIn("w-[280px]", self.page_source)
        self.assertIn("bg-black/60 backdrop-blur-sm lg:hidden", self.page_source)

    def test_keyboard_shortcuts(self):
        self.assertIn("e.key.toLowerCase() === 'b'", self.page_source)
        self.assertIn("e.key === 'Escape'", self.page_source)

    def test_temporal_grouping_categories(self):
        self.assertIn("{ label: 'Hoje', items: [] }", self.page_source)
        self.assertIn("{ label: 'Ontem', items: [] }", self.page_source)
        self.assertIn("{ label: 'Últimos 7 dias', items: [] }", self.page_source)
        self.assertIn("{ label: 'Mais antigas', items: [] }", self.page_source)

    def test_stop_generation_abort_controller(self):
        self.assertIn("abortControllerRef.current?.abort()", self.page_source)
        self.assertIn("Parar", self.page_source)

    def test_drag_and_drop_and_size_validation(self):
        self.assertIn("onDragOver={handleDragOver}", self.page_source)
        self.assertIn("onDrop={handleDrop}", self.page_source)
        self.assertIn("10 * 1024 * 1024", self.page_source)

    def test_differentiated_error_handling(self):
        self.assertIn("err.status === 401", self.page_source)
        self.assertIn("err.status === 429", self.page_source)
        self.assertIn("err.status === 503", self.page_source)
        self.assertIn("tentarNovamente", self.page_source)

    def test_server_verified_provider_badge(self):
        self.assertIn("data.provider_used !== 'fallback'", self.page_source)
        self.assertIn("Contingência", self.page_source)

    def test_responsive_viewport_invariants_360_768_1280(self):
        # 360px Mobile
        self.assertIn("lg:hidden", self.page_source)
        self.assertIn("backdrop-blur-sm", self.page_source)
        # 768px / Tablet / Mobile breakpoints
        self.assertIn("sm:", self.page_source)
        # 1280px Desktop & container constraints
        self.assertIn("w-[280px]", self.page_source)
        self.assertIn("max-w-3xl", self.page_source)

if __name__ == "__main__":
    unittest.main()
