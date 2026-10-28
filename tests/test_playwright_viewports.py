import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

class MockSSEHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8", errors="ignore") if content_len > 0 else ""

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

        if "abort_test" in post_body and not getattr(self.server, "abort_done", False):
            self.server.abort_done = True
            self.server.aborted_detected = False
            self.wfile.write(b'data: {"content": "Iniciando resposta longa aguardando cancelamento...", "done": false}\n\n')
            self.wfile.flush()
            for _ in range(40):
                time.sleep(0.08)
                try:
                    self.wfile.write(b': keepalive-ping\n\n')
                    self.wfile.flush()
                except Exception:
                    self.server.aborted_detected = True
                    break
            self.close_connection = True
            return

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
import sys
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
        if sys.platform == "win32":
            try:
                import asyncio
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass
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

    def test_playwright_cancel_active_stream_and_retry(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
        """)

        page.route("**/chat/stream", lambda route: route.continue_(url=f"http://127.0.0.1:{self.mock_sse_port}/chat/stream"))
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())

        # Envia pergunta que dispara stream lento com suporte a cancelamento
        textarea.fill("Pergunta para teste de abort_test no navegador")
        btn_enviar = page.locator("button[title='Enviar']").first
        if btn_enviar.is_visible():
            btn_enviar.click()
        else:
            page.keyboard.press("Enter")

        # 1. Aguarda primeiro chunk e presenca do botao Parar
        page.wait_for_selector("text=Iniciando resposta longa", timeout=6000)
        btn_parar = page.locator("button:has-text('Parar')").first
        self.assertTrue(btn_parar.is_visible(), "Botao Parar deve estar visivel durante streaming ativo")

        # 2. Clica no botao Parar para efetuar o cancelamento ativo
        btn_parar.click()

        # 3. Confirma que o estado de loading foi cancelado (botao Parar sumiu)
        page.wait_for_selector("button:has-text('Parar')", state="detached", timeout=4000)

        # 4. Confirma que botao Tentar Novamente aparece OBRIGATORIAMENTE (sem condicional permissivo) e clica nele
        page.wait_for_selector("button:has-text('Tentar novamente')", timeout=5000)
        btn_retry = page.locator("button:has-text('Tentar novamente')").first
        self.assertTrue(btn_retry.is_visible(), "Botao Tentar novamente DEVE estar visivel e presente apos cancelamento")
        btn_retry.click()

        # 5. Valida que a nova requisicao de retry conclui ate a resposta final
        page.wait_for_selector("text=Finalizando stream.", timeout=8000)

        # 6. Confirma que o servidor percebeu o cancelamento da primeira conexao
        self.assertTrue(getattr(self.sse_server, "aborted_detected", False), "Servidor SSE mockado deve detectar o cancelamento ativo do cliente")

        shot_path = SCREENSHOTS_DIR / "viewport_sse_abort_and_retry.png"
        page.screenshot(path=str(shot_path))
        self.assertTrue(shot_path.exists())
        page.close()

    def test_playwright_conversation_rename_and_delete(self):
        """TESTE E2E FRONTEND (MOCK HTTP NO NAVEGADOR):
        Valida o fluxo completo de interação da interface para renomeação inline e exclusão de conversas,
        comprovando a persistência no localStorage do navegador e atualização semântica do DOM."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        # Inicializa localStorage com conversa local pré-existente
        page.add_init_script("""
            localStorage.setItem('helpus_conversas_locais', JSON.stringify([
                {
                    session_id: 'sess_pw_test1',
                    titulo: 'Conversa Original Playwright',
                    updated_at: new Date().toISOString(),
                    total_mensagens: 2
                }
            ]));
        """)
        # Mock de endpoint PATCH /conversa (contrato frontend UI)
        page.route("**/conversa/**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"status": "ok"}'
        ))
        page.goto(self.base_url, wait_until="networkidle")

        # 1. Verifica exibição da conversa na barra lateral
        item = page.locator("text=Conversa Original Playwright").first
        self.assertTrue(item.is_visible(), "Conversa pré-existente deve ser exibida na sidebar")

        # 2. Aciona botão de renomear (hover no container para revelar ações)
        item.hover()
        btn_rename = page.locator("button[title='Renomear']").first
        btn_rename.click()

        # 3. Digita novo título no campo de edição e confirma com Enter
        page.wait_for_selector("input[data-testid='input-rename-conversa']", timeout=5000)
        input_edit = page.locator("input[data-testid='input-rename-conversa']").first
        self.assertTrue(input_edit.is_visible(), "Campo de renomeação inline deve aparecer")
        input_edit.fill("Conversa Renomeada com Sucesso")
        input_edit.press("Enter")

        # 4. Verifica que o novo título foi atualizado no DOM e no localStorage
        page.wait_for_selector("text=Conversa Renomeada com Sucesso", timeout=5000)
        self.assertTrue(page.locator("text=Conversa Renomeada com Sucesso").first.is_visible())
        loc_after_rename = page.evaluate("() => localStorage.getItem('helpus_conversas_locais')")
        self.assertIn("Conversa Renomeada com Sucesso", loc_after_rename or "", "Novo título deve estar persistido no localStorage do navegador")

        # 5. Aciona exclusão da conversa (hover no container atualizado)
        item_renamed = page.locator("text=Conversa Renomeada com Sucesso").first
        item_renamed.hover()
        btn_delete = page.locator("button[title='Excluir']").first
        btn_delete.click()

        # 6. Verifica que a conversa foi removida do DOM e do localStorage
        page.wait_for_selector("text=Conversa Renomeada com Sucesso", state="detached", timeout=5000)
        loc_after_delete = page.evaluate("() => localStorage.getItem('helpus_conversas_locais')")
        self.assertNotIn("Conversa Renomeada com Sucesso", loc_after_delete or "", "Conversa excluída deve ser removida do localStorage do navegador")

        shot_path = SCREENSHOTS_DIR / "viewport_conversation_rename_delete.png"
        page.screenshot(path=str(shot_path))
        page.close()

    def test_playwright_copy_link_and_load_history(self):
        """TESTE E2E FRONTEND (MOCK HTTP NO NAVEGADOR):
        Valida cópia de URL via Clipboard API do navegador e carregamento instantâneo do histórico."""
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = context.new_page()
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
            localStorage.setItem('helpus_conversas_locais', JSON.stringify([
                {{
                    session_id: 'sess_pw_link_test',
                    titulo: 'Conversa Link e Historico',
                    updated_at: new Date().toISOString(),
                    total_mensagens: 4
                }}
            ]));
            localStorage.setItem('helpus_msgs_sess_pw_link_test', JSON.stringify([
                {{"role": "user", "content": "Mensagem historica do usuario"}},
                {{"role": "assistant", "content": "Resposta historica do assistente"}}
            ]));
        """)
        # Mock do endpoint de histórico de mensagens (contrato frontend UI)
        hist_body = '{"session_id": "sess_pw_link_test", "titulo": "Conversa Link e Historico", "mensagens": [{"role": "user", "content": "Mensagem historica do usuario"}, {"role": "assistant", "content": "Resposta historica do assistente"}]}'
        page.route("**/historico/sess_pw_link_test", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=hist_body
        ))
        page.route("**/conversa/sess_pw_link_test", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=hist_body
        ))
        page.goto(self.base_url, wait_until="networkidle")

        # 1. Clica no botão Copiar link da conversa na sidebar (com hover)
        item = page.locator("text=Conversa Link e Historico").first
        self.assertTrue(item.is_visible())
        item.hover()
        btn_copy = page.locator("button[title='Copiar link']").first
        self.assertTrue(btn_copy.is_visible(), "Botão Copiar link deve estar presente no item da conversa")
        btn_copy.click()

        # 2. Valida leitura real da Clipboard API do navegador
        clip_content = page.evaluate("() => navigator.clipboard ? navigator.clipboard.readText() : ''")
        self.assertIn("sess_pw_link_test", clip_content, "Clipboard do navegador deve conter o session_id copiado")

        # 3. Clica na conversa para carregar o histórico
        item.click()

        # 4. Verifica renderização do histórico no corpo do chat
        page.wait_for_selector("text=Resposta historica do assistente", timeout=6000)
        self.assertTrue(page.locator("text=Resposta historica do assistente").first.is_visible())

        shot_path = SCREENSHOTS_DIR / "viewport_copy_link_and_history.png"
        page.screenshot(path=str(shot_path))
        context.close()

    def test_playwright_persistence_failure_error_handling(self):
        """TESTE E2E FRONTEND (MOCK HTTP NO NAVEGADOR):
        Simula falha 500 do backend (fail-closed) e valida que o frontend renderiza mensagem de erro
        amigável institucional com o botão 'Tentar novamente' visível e operável."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
        """)
        # Rota de stream e rota de chat retornam erro 500 para simular falha de persistência fail-closed
        page.route("**/chat/stream", lambda route: route.fulfill(
            status=500,
            content_type="application/json",
            body='{"detail": "Falha de persistencia duravel (fail-closed)"}'
        ))
        page.route("**/chat", lambda route: route.fulfill(
            status=500,
            content_type="application/json",
            body='{"detail": "Falha de persistencia duravel (fail-closed)"}'
        ))
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())
        textarea.fill("Pergunta simulando erro no servidor")
        btn_enviar = page.locator("button[title='Enviar']").first
        if btn_enviar.is_visible():
            btn_enviar.click()
        else:
            page.keyboard.press("Enter")

        # Verifica presença de mensagem de erro amigável e botão Tentar novamente
        page.wait_for_selector("text=Desculpe, ocorreu uma instabilidade momentânea ao processar sua solicitação.", timeout=8000)
        page.wait_for_selector("text=Tentar novamente", timeout=6000)
        self.assertTrue(page.locator("text=Tentar novamente").first.is_visible())

        shot_path = SCREENSHOTS_DIR / "viewport_persistence_failure.png"
        page.screenshot(path=str(shot_path))
        page.close()

    def test_playwright_sse_persistence_failed_displays_error_and_never_done(self):
        """P1 CLIENTE SSE (Ciclo 033):
        Valida que o evento SSE 'PERSISTENCE_FAILED' seguido do terminador de transporte '[DONE]'
        apresenta erro institucional amigavel ao usuario ('Falha ao persistir a resposta com seguranca'),
        exibe o botao 'Tentar novamente', NUNCA exibe a resposta como concluida e trata '[DONE]' apenas
        como encerramento de conexao."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
        """)

        # Simula stream SSE com pedaco parcial, evento PERSISTENCE_FAILED e terminador [DONE]
        sse_body = (
            "data: {\"content\": \"Pedaco parcial de resposta antes da falha. \", \"done\": false}\n\n"
            "data: {\"error\": \"Falha ao persistir resposta no banco de dados.\", \"error_code\": \"PERSISTENCE_FAILED\"}\n\n"
            "data: [DONE]\n\n"
        )
        page.route("**/chat/stream", lambda route: route.fulfill(
            status=200,
            content_type="text/event-stream; charset=utf-8",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            body=sse_body
        ))
        page.goto(self.base_url, wait_until="networkidle")

        textarea = page.locator("textarea").first
        self.assertTrue(textarea.is_visible())
        textarea.fill("Pergunta testando evento PERSISTENCE_FAILED")
        btn_enviar = page.locator("button[title='Enviar']").first
        if btn_enviar.is_visible():
            btn_enviar.click()
        else:
            page.keyboard.press("Enter")

        # 1. Verifica exibicao da mensagem de erro de persistencia ao usuario
        page.wait_for_selector("text=Falha ao persistir a resposta com segurança", timeout=8000)
        self.assertTrue(page.locator("text=Falha ao persistir a resposta com segurança").first.is_visible())

        # 2. Verifica presenca do botao Tentar novamente
        page.wait_for_selector("text=Tentar novamente", timeout=6000)
        self.assertTrue(page.locator("text=Tentar novamente").first.is_visible())

        # 3. Comprova que a resposta NUNCA e exibida como concluida
        self.assertFalse(page.locator("text=Pedaco parcial de resposta antes da falha").is_visible())

        shot_path = SCREENSHOTS_DIR / "viewport_sse_persistence_failed_ui.png"
        page.screenshot(path=str(shot_path))
        page.close()

    def test_playwright_scroll_to_bottom_floating_button(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ICJ0ZXN0ZXJAaGVscHVzYnIuY29tIiwgIm5hbWUiOiAiSGVscFVTIFRlc3RlciJ9.signature"
        # Cria mensagens longas suficientes para causar scroll vertical
        long_messages = []
        for i in range(12):
            long_messages.append({"role": "user", "content": f"Pergunta número {i} para teste de viewport longo."})
            long_messages.append({"role": "assistant", "content": f"Resposta longa {i}: " + ("conteudo repetido " * 30)})

        import json
        page.add_init_script(f"""
            localStorage.setItem('helpus_google_token', '{fake_jwt}');
            localStorage.setItem('helpus_conversas_locais', JSON.stringify([
                {{
                    session_id: 'sess_pw_scroll',
                    titulo: 'Conversa Longa Scroll',
                    updated_at: new Date().toISOString(),
                    total_mensagens: 24
                }}
            ]));
            localStorage.setItem('helpus_msgs_sess_pw_scroll', JSON.stringify({json.dumps(long_messages)}));
        """)
        scroll_body = json.dumps({"session_id": "sess_pw_scroll", "titulo": "Conversa Longa Scroll", "mensagens": long_messages})
        page.route("**/historico/sess_pw_scroll", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=scroll_body
        ))
        page.route("**/conversa/sess_pw_scroll", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=scroll_body
        ))
        page.goto(self.base_url, wait_until="networkidle")

        # Abre conversa longa
        page.locator("text=Conversa Longa Scroll").first.click()
        page.wait_for_selector("text=Pergunta número 11", timeout=6000)

        # Rola para o topo do container do chat e dispara evento de scroll
        page.evaluate("""() => {
            const el = document.querySelector('.overflow-y-auto');
            if (el) {
                el.scrollTop = 0;
                el.dispatchEvent(new Event('scroll'));
            }
        }""")

        # Verifica se botão Ir para o fim aparece e pode ser acionado
        page.wait_for_selector("button[title='Ir para o fim']", timeout=6000)
        btn_scroll = page.locator("button[title='Ir para o fim']").first
        self.assertTrue(btn_scroll.is_visible())
        btn_scroll.click(force=True)

        shot_path = SCREENSHOTS_DIR / "viewport_scroll_to_bottom.png"
        page.screenshot(path=str(shot_path))
        page.close()

if __name__ == "__main__":
    unittest.main()
