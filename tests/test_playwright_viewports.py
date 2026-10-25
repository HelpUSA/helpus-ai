"""Real browser Playwright end-to-end tests across 360px, 768px, and 1280px viewports."""
import unittest
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"

class PlaywrightViewportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.port = 3088
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.proc = subprocess.Popen(
            ["npx.cmd", "next", "start", "-p", str(cls.port)],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ready = False
        for _ in range(24):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(cls.base_url, timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                pass
        if not ready:
            cls.proc.terminate()
            raise RuntimeError("Next.js frontend server failed to start within timeout.")
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "browser"):
            cls.browser.close()
        if hasattr(cls, "playwright"):
            cls.playwright.stop()
        if hasattr(cls, "proc"):
            cls.proc.terminate()
            try:
                cls.proc.wait(timeout=3)
            except Exception:
                cls.proc.kill()

    def test_viewport_360_mobile(self):
        page = self.browser.new_page(viewport={"width": 360, "height": 640})
        page.goto(self.base_url, wait_until="networkidle")
        self.assertIn("HelpUS", page.title() or page.content())

        # Verifica ausencia de overflow horizontal no mobile
        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        self.assertLessEqual(scroll_width, 362)

        # Verifica presenca da textarea de prompt
        textarea = page.locator("textarea")
        self.assertTrue(textarea.count() >= 1)

        shot_path = SCREENSHOTS_DIR / "viewport_360_mobile.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

    def test_viewport_768_tablet(self):
        page = self.browser.new_page(viewport={"width": 768, "height": 1024})
        page.goto(self.base_url, wait_until="networkidle")

        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        self.assertLessEqual(scroll_width, 770)

        shot_path = SCREENSHOTS_DIR / "viewport_768_tablet.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

    def test_viewport_1280_desktop(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(self.base_url, wait_until="networkidle")

        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        self.assertLessEqual(scroll_width, 1282)

        shot_path = SCREENSHOTS_DIR / "viewport_1280_desktop.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

if __name__ == "__main__":
    unittest.main()
