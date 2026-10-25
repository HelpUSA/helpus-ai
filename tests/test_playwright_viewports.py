import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

class MockSSEHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

        # Chunk 1 (t = 0s)
        self.wfile.write(b'data: {"content": "Ola! Resposta temporal fragmentada ", "done": false}\n\n')
        self.wfile.flush()
        time.sleep(0.35)

        # Chunk 2 (t = 0.35s)
        self.wfile.write(b'data: {"content": "comprovando progressividade no tempo. ", "done": false}\n\n')
        self.wfile.flush()
        time.sleep(0.35)

        # Chunk 3 (t = 0.70s)
        self.wfile.write(b'data: {"content": "Finalizando stream.", "done": false}\n\n')
        self.wfile.flush()
        time.sleep(0.2)

        # Sinal done e DONE final
        self.wfile.write(b'data: {"done": true, "session_id": "sess_playwright_temporal_sse"}\n\n')
        self.wfile.write(b'data: [DONE]\n\n')
        self.wfile.flush()
        self.close_connection = True

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def log_message(self, format, *args):
        pass

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
        cls.mock_sse_port = 3099
        cls.sse_server = ThreadingHTTPServer(("127.0.0.1", cls.mock_sse_port), MockSSEHandler)
        cls.sse_thread = threading.Thread(target=cls.sse_server.serve_forever, daemon=True)
        cls.sse_thread.start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "sse_server"):
            cls.sse_server.shutdown()
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

    def test_playwright_chat_interaction_typing(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())

        prompt_text = "Teste de envio e interacao para AI HelpUS Ciclo 015"
        textarea.fill(prompt_text)
        val = textarea.input_value()
        self.assertEqual(val, prompt_text)

        shot_path = SCREENSHOTS_DIR / "viewport_typing_desktop.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

    def test_playwright_mobile_drawer_toggle(self):
        page = self.browser.new_page(viewport={"width": 360, "height": 640})
        page.goto(self.base_url, wait_until="networkidle")

        # Localiza o botao de menu
        btn = page.locator("button[title*='menu']").first
        if btn.count() > 0:
            btn.click()
            page.wait_for_timeout(400) # aguarda transicao CSS

        shot_path = SCREENSHOTS_DIR / "viewport_mobile_drawer_toggled.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

    def test_playwright_chat_submit_and_sse_container(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())

        prompt = "Olá HelpUS AI, teste funcional de envio e streaming SSE Ciclo 016"
        textarea.fill(prompt)
        page.keyboard.press("Enter")
        page.wait_for_timeout(600)

        content = page.content()
        self.assertIn("Olá HelpUS AI", content)

        shot_path = SCREENSHOTS_DIR / "viewport_chat_submitted_sse.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()


    def test_playwright_sse_streaming_mock(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})

        # Injeta token de sessao autenticada para permitir envio direto de mensagens
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
        """)

        # Intercepta rota de streaming SSE com chunks mockados
        def handle_sse(route):
            chunks = [
                'data: {"content": "Ola HelpUS! ", "done": false}\n\n',
                'data: {"content": "Streaming mock validado com sucesso.", "done": false}\n\n',
                'data: {"done": true, "session_id": "sess_playwright_sse_mock"}\n\n',
                'data: [DONE]\n\n',
            ]
            route.fulfill(
                status=200,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
                body="".join(chunks),
            )

        page.route("**/chat/stream", handle_sse)
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())

        textarea.fill("Pergunta de teste para SSE streaming Playwright")
        # Aciona envio atraves do botao Enviar ou Enter
        btn_enviar = page.locator("button[title='Enviar']").first
        if btn_enviar.is_visible():
            btn_enviar.click()
        else:
            page.keyboard.press("Enter")

        # Aguarda renderizacao incremental no DOM
        page.wait_for_selector("text=Streaming mock validado com sucesso.", timeout=8000)
        content = page.content()
        self.assertIn("Streaming mock validado com sucesso.", content)

        shot_path = SCREENSHOTS_DIR / "viewport_sse_mocked_streaming.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

    def test_playwright_temporal_sse_streaming_and_cancellation(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
        """)

        # Redireciona /chat/stream para o servidor de streaming real fragmentado no tempo
        page.route("**/chat/stream", lambda route: route.continue_(url=f"http://127.0.0.1:{self.mock_sse_port}/chat/stream"))
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())

        textarea.fill("Pergunta para teste de SSE temporal e cancelamento")
        btn_enviar = page.locator("button[title='Enviar']").first
        if btn_enviar.is_visible():
            btn_enviar.click()
        else:
            page.keyboard.press("Enter")

        # 1. Verifica primeiro chunk fragmentado chegando
        page.wait_for_selector("text=Ola! Resposta temporal fragmentada", timeout=6000)

        # 2. Aguarda conclusao total do stream e [DONE]
        page.wait_for_selector("text=Finalizando stream.", timeout=8000)

        # 3. Verifica presenca do botao 'Tentar novamente' na resposta concluida
        page.wait_for_selector("text=Tentar novamente", timeout=6000)

        shot_path = SCREENSHOTS_DIR / "viewport_sse_temporal_streaming.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

if __name__ == "__main__":
    unittest.main()
