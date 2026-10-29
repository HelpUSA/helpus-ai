# -*- coding: utf-8 -*-
"""Suíte de Testes Unitários de Segurança OAuth / JWT Google — Ordens 082 e 084.

Validações isoladas sem rede externa, sem bancos remotos e sem credenciais reais:
1. Rejeição de tokens falsificados com payload manipulado (antigo fallback eliminado)
2. Rejeição de assinatura criptográfica inválida
3. Rejeição de audiência incorreta (aud mismatch)
4. Rejeição de token expirado (exp)
5. Rejeição de emissor não autorizado (iss mismatch)
6. Rejeição de token sem email
7. Matriz estrita de validação de email_verified (Ordem 084):
   - email_verified ausente -> 401 unverified_email
   - email_verified = None -> 401 unverified_email
   - email_verified = "false" -> 401 unverified_email
   - email_verified = "true" (string) -> 401 unverified_email
   - email_verified = 0 -> 401 unverified_email
   - email_verified = False (booleano) -> 401 unverified_email
   - email_verified = True (booleano estrito) -> aceito
8. Rejeição de token sem sub (subject)
9. Aceitação de token íntegro e verificado oficialmente
10. Verificação de que verify_oauth2_token recebe o GOOGLE_CLIENT_ID esperado e que falha bloqueia autenticação
11. Bloqueio de elevação de privilégio administrativo via token forjado
12. Proibição de acesso administrativo para usuário legítimo não cadastrado (403)
13. Acesso administrativo concedido para email presente em ADMIN_EMAILS
14. Tratamento seguro de token ausente, vazio ou whitespace
15. Fail-closed caso GOOGLE_CLIENT_ID não esteja configurado
16. Paridade estrita entre backend/auth.py e api/auth.py (eliminação do fallback e checagem is True)
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

import backend.auth as auth_backend
import api.auth as auth_api


class TestOAuthJwtSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_client_id = "812202824664-test.apps.googleusercontent.com"
        self.admin_email = "admin@helpusbr.com"
        self.user_email = "cliente@helpusbr.com"

    def test_forged_unverified_token_rejected_in_backend(self):
        """Um token forjado com payload manipulado que falha na verificação oficial
        DEVE ser rejeitado com 401 e NUNCA ser decodificado via fallback inseguro."""
        fake_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJlbWFpbCI6ImFkbWluQGhlbHB1c2JyLmNvbSIsInN1YiI6ImZvcmdlZDEyMyJ9.fakesignature"
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Invalid crypto signature")):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token(fake_token)
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_forged_unverified_token_rejected_in_api_mirror(self):
        """Paridade: api/auth.py também deve rejeitar o token forjado com 401."""
        fake_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJlbWFpbCI6ImFkbWluQGhlbHB1c2JyLmNvbSIsInN1YiI6ImZvcmdlZDEyMyJ9.fakesignature"
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Invalid crypto signature")):
            with patch.object(auth_api, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_api.verificar_google_id_token(fake_token)
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_invalid_signature_rejected(self):
        """Falha de assinatura criptográfica deve disparar 401 fail-closed."""
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Signature verification failed")):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.bad_payload.bad_sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_incorrect_audience_rejected(self):
        """Token emitido para outro Client ID (aud mismatch) deve ser rejeitado com 401."""
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Wrong audience")):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.wrong_aud_payload.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_expired_token_rejected(self):
        """Token expirado deve ser rejeitado com 401."""
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Token expired")):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.expired_payload.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_invalid_issuer_rejected(self):
        """Emissor que não seja Google deve ser rejeitado com 401."""
        untrusted_payload = {
            "iss": "https://evil.untrusted-issuer.com",
            "sub": "evil_sub_999",
            "email": "attacker@evil.com",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=untrusted_payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.untrusted_iss.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_missing_email_rejected(self):
        """Token válido sem claim de email deve ser rejeitado com 401."""
        payload_no_email = {
            "iss": "https://accounts.google.com",
            "sub": "valid_sub_123",
            "email": "",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload_no_email):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.no_email.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    # --- Testes de Matriz Estrita para email_verified (Ordem 084) ---

    def test_email_verified_missing_rejected(self):
        """Ordem 084: email_verified ausente no payload DEVE ser rejeitado com 401 unverified_email."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_no_verified_claim",
            "email": "user@gmail.com",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.missing_verified.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "unverified_email")

    def test_email_verified_none_rejected(self):
        """Ordem 084: email_verified=None DEVE ser rejeitado com 401 unverified_email."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_none_verified",
            "email": "user@gmail.com",
            "email_verified": None,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.none_verified.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "unverified_email")

    def test_email_verified_string_false_rejected(self):
        """Ordem 084: email_verified='false' (string) DEVE ser rejeitado com 401 unverified_email."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_str_false",
            "email": "user@gmail.com",
            "email_verified": "false",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.str_false.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "unverified_email")

    def test_email_verified_string_true_rejected(self):
        """Ordem 084: email_verified='true' (string não-booleana) DEVE ser rejeitado com 401 unverified_email."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_str_true",
            "email": "user@gmail.com",
            "email_verified": "true",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.str_true.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "unverified_email")

    def test_email_verified_zero_rejected(self):
        """Ordem 084: email_verified=0 (inteiro) DEVE ser rejeitado com 401 unverified_email."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_int_zero",
            "email": "user@gmail.com",
            "email_verified": 0,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.int_zero.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "unverified_email")

    def test_email_verified_boolean_false_rejected(self):
        """Ordem 084: email_verified=False (booleano) DEVE ser rejeitado com 401 unverified_email."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_bool_false",
            "email": "unverified@gmail.com",
            "email_verified": False,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.bool_false.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "unverified_email")

    def test_email_verified_boolean_true_accepted(self):
        """Ordem 084: Apenas o booleano True estrito deve ser aceito como verificado."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_verified_ok",
            "email": "verified@helpusbr.com",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                user = auth_backend.verificar_google_id_token("header.verified_ok.sig")
                self.assertEqual(user["email"], "verified@helpusbr.com")

    # --- Verificação do Parâmetro Audience e Fail-Closed do Verificador (Ordem 084) ---

    def test_verify_oauth2_token_receives_expected_client_id(self):
        """Ordem 084: Confirma que verify_oauth2_token é invocado com o GOOGLE_CLIENT_ID esperado."""
        payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_aud_test",
            "email": "test@helpusbr.com",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload) as mock_verify:
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                auth_backend.verificar_google_id_token("test_token_content")
                mock_verify.assert_called_once()
                args, kwargs = mock_verify.call_args
                # args: (token, request, audience)
                self.assertEqual(args[0], "test_token_content")
                self.assertEqual(args[2], self.mock_client_id)

    def test_verify_oauth2_token_failure_strictly_prevents_authentication(self):
        """Ordem 084: Qualquer falha interna ou de transporte em verify_oauth2_token
        impede absolutamente a autenticação (fail-closed) sem retorno de usuário."""
        from google.auth.exceptions import GoogleAuthError
        for exc in (ValueError("Signature corrupted"), GoogleAuthError("Certs fetch timeout"), RuntimeError("Unexpected error")):
            with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=exc):
                with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                    with self.assertRaises(HTTPException) as ctx:
                        auth_backend.verificar_google_id_token("token_error_case")
                    self.assertEqual(ctx.exception.status_code, 401)
                    self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_missing_sub_rejected(self):
        """Token sem claim sub deve ser rejeitado com 401."""
        payload_no_sub = {
            "iss": "https://accounts.google.com",
            "sub": "",
            "email": "user@gmail.com",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=payload_no_sub):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with self.assertRaises(HTTPException) as ctx:
                    auth_backend.verificar_google_id_token("header.no_sub.sig")
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

    def test_valid_verified_token_success(self):
        """Token assinado e verificado com sucesso deve retornar perfil normalizado."""
        valid_payload = {
            "iss": "https://accounts.google.com",
            "sub": "google_sub_7890",
            "email": "User@HelpUsBR.com",
            "name": "Usuario Teste",
            "picture": "https://lh3.googleusercontent.com/avatar.png",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=valid_payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                user = auth_backend.verificar_google_id_token("header.valid_token.sig")
                self.assertEqual(user["sub"], "google_sub_7890")
                self.assertEqual(user["email"], "user@helpusbr.com")
                self.assertEqual(user["name"], "Usuario Teste")
                self.assertEqual(user["picture"], "https://lh3.googleusercontent.com/avatar.png")

    def test_admin_endpoint_with_forged_token_rejected(self):
        """Acesso administrativo via token forjado deve ser bloqueado com 401 fail-closed."""
        import asyncio
        fake_token = "Bearer header.forged_admin_payload.sig"
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Bad signature")):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with patch.object(auth_backend, "ADMIN_EMAILS", [self.admin_email]):
                    with self.assertRaises(HTTPException) as ctx:
                        asyncio.run(auth_backend.obter_admin_google(fake_token))
                    self.assertEqual(ctx.exception.status_code, 401)

    def test_admin_endpoint_with_valid_non_admin_token_forbidden(self):
        """Usuário autenticado cujo email não está em ADMIN_EMAILS deve receber 403 Forbidden."""
        import asyncio
        valid_non_admin_payload = {
            "iss": "accounts.google.com",
            "sub": "sub_regular_user",
            "email": self.user_email,
            "email_verified": True,
        }
        token_str = "Bearer valid.non_admin.sig"
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=valid_non_admin_payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with patch.object(auth_backend, "ADMIN_EMAILS", [self.admin_email]):
                    with self.assertRaises(HTTPException) as ctx:
                        asyncio.run(auth_backend.obter_admin_google(token_str))
                    self.assertEqual(ctx.exception.status_code, 403)
                    self.assertEqual(ctx.exception.detail.get("error"), "admin_forbidden")

    def test_admin_endpoint_with_valid_admin_token_accepted(self):
        """Administrador com token verificado e email na allowlist recebe perfil."""
        import asyncio
        valid_admin_payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_admin_master",
            "email": self.admin_email,
            "name": "Super Admin",
            "email_verified": True,
        }
        token_str = "Bearer valid.admin.sig"
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=valid_admin_payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with patch.object(auth_backend, "ADMIN_EMAILS", [self.admin_email]):
                    admin = asyncio.run(auth_backend.obter_admin_google(token_str))
                    self.assertEqual(admin["email"], self.admin_email)
                    self.assertEqual(admin["sub"], "sub_admin_master")

    def test_empty_or_whitespace_token_rejected(self):
        """Tokens vazios ou compostos exclusivamente de espaços devem ser rejeitados com 401."""
        for empty_val in ("", "   ", None):
            with self.assertRaises(HTTPException) as ctx:
                auth_backend.verificar_google_id_token(empty_val)
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertEqual(ctx.exception.detail.get("error"), "missing_google_token")

    def test_missing_client_id_configuration_fails_closed(self):
        """Se GOOGLE_CLIENT_ID estiver desconfigurado (vazio), falhar seguro com 500."""
        with patch.object(auth_backend, "GOOGLE_CLIENT_ID", ""):
            with self.assertRaises(HTTPException) as ctx:
                auth_backend.verificar_google_id_token("some.token.value")
            self.assertEqual(ctx.exception.status_code, 500)
            self.assertEqual(ctx.exception.detail.get("error"), "oauth_configuration_error")

    def test_mirror_api_and_backend_auth_parity(self):
        """Verifica estrita paridade e garante ausência total do fallback inseguro em ambos."""
        for path in [ROOT / "api" / "auth.py", ROOT / "backend" / "auth.py"]:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("base64.urlsafe_b64decode", content, f"Fallback inseguro encontrado em {path}")
            self.assertNotIn("parts = token.split", content, f"Split manual inseguro de JWT em {path}")
            self.assertIn("verify_oauth2_token", content)
            self.assertIn('info.get("email_verified") is not True', content, f"Checagem estrita ausente em {path}")
            self.assertIn("sub", content)

    def test_integrated_account_isolation_flow(self):
        """Ordem 085: Valida que dois usuários (Alice e Bob) com tokens distintos possuem
        identidades, subs e emails rigorosamente segregados, sem vazamento mútuo."""
        import asyncio
        alice_payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_alice_12345",
            "email": "alice@helpusbr.com",
            "name": "Alice Silva",
            "email_verified": True,
        }
        bob_payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_bob_67890",
            "email": "bob@helpusbr.com",
            "name": "Bob Souza",
            "email_verified": True,
        }

        def mock_verify_by_token(token, req, aud):
            if token == "token_alice":
                return alice_payload
            elif token == "token_bob":
                return bob_payload
            raise ValueError("Token desconhecido")

        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=mock_verify_by_token):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                user_alice = asyncio.run(auth_backend.obter_usuario_google("Bearer token_alice"))
                user_bob = asyncio.run(auth_backend.obter_usuario_google("Bearer token_bob"))

                self.assertIsNotNone(user_alice)
                self.assertIsNotNone(user_bob)
                self.assertEqual(user_alice["email"], "alice@helpusbr.com")
                self.assertEqual(user_alice["sub"], "sub_alice_12345")
                self.assertEqual(user_bob["email"], "bob@helpusbr.com")
                self.assertEqual(user_bob["sub"], "sub_bob_67890")
                self.assertNotEqual(user_alice["sub"], user_bob["sub"])
                self.assertNotEqual(user_alice["email"], user_bob["email"])

    def test_token_renewal_flow(self):
        """Ordem 085: Simula token expirado sendo rejeitado (401), seguido por renovação
        com emissão de novo token válido aceito com sucesso."""
        import asyncio
        renewed_payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_renewed_user",
            "email": "usuario@helpusbr.com",
            "name": "Usuario Renovado",
            "email_verified": True,
        }

        def mock_verify_flow(token, req, aud):
            if token == "expired_token_1":
                raise ValueError("Token is expired")
            elif token == "fresh_renewed_token_2":
                return renewed_payload
            raise ValueError("Invalid token")

        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=mock_verify_flow):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                # 1. Tentativa com token expirado -> falha com 401
                with self.assertRaises(HTTPException) as ctx:
                    asyncio.run(auth_backend.obter_usuario_google("Bearer expired_token_1"))
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail.get("error"), "invalid_google_token")

                # 2. Cliente renova token e reenvia -> sucesso
                user = asyncio.run(auth_backend.obter_usuario_google("Bearer fresh_renewed_token_2"))
                self.assertIsNotNone(user)
                self.assertEqual(user["email"], "usuario@helpusbr.com")
                self.assertEqual(user["sub"], "sub_renewed_user")

    def test_logout_flow_and_subsequent_request(self):
        """Ordem 085: Simula logout do cliente (remoção do cabeçalho de autorização).
        Em AUTH_REQUIRED=True, subsequente requisição deve falhar com 401 auth_required.
        Em AUTH_REQUIRED=False, subsequente requisição retorna None (anônimo)."""
        import asyncio
        with patch.object(auth_backend, "AUTH_REQUIRED", True):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(auth_backend.obter_usuario_google(None))
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertEqual(ctx.exception.detail.get("error"), "auth_required")

        with patch.object(auth_backend, "AUTH_REQUIRED", False):
            anon = asyncio.run(auth_backend.obter_usuario_google(None))
            self.assertIsNone(anon)

    def test_admin_endpoint_denies_access_when_admin_allowlist_is_empty(self):
        """Ordem 085: Se ADMIN_EMAILS estiver vazio ([]), obter_admin_google deve
        falhar fechado com 403 admin_forbidden para qualquer usuário."""
        import asyncio
        valid_user_payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_user_attempting_admin",
            "email": "user@helpusbr.com",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=valid_user_payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with patch.object(auth_backend, "ADMIN_EMAILS", []):
                    with self.assertRaises(HTTPException) as ctx:
                        asyncio.run(auth_backend.obter_admin_google("Bearer valid.token.sig"))
                    self.assertEqual(ctx.exception.status_code, 403)
                    self.assertEqual(ctx.exception.detail.get("error"), "admin_forbidden")

    def test_environment_fail_closed_validation_strategy(self):
        """Ordem 085/086: Avalia a política de segurança e fail-closed da configuração por ambiente."""
        import backend.config as b_cfg

        # 1. Produção com AUTH_REQUIRED=False deve acusar não-conformidade (risco alto)
        with patch.object(b_cfg, "ENVIRONMENT", "production"):
            with patch.object(b_cfg, "AUTH_REQUIRED", False):
                with patch.object(b_cfg, "GOOGLE_CLIENT_ID", self.mock_client_id):
                    diag = b_cfg.validar_politica_seguranca_ambiente(enforce=False)
                    self.assertFalse(diag["conforme"])
                    self.assertTrue(any("AUTH_REQUIRED" in err for err in diag["erros"]))

        # 2. Produção com AUTH_REQUIRED=True e GOOGLE_CLIENT_ID configurado deve estar conforme
        with patch.object(b_cfg, "ENVIRONMENT", "production"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": self.mock_client_id}):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", self.mock_client_id):
                        with patch.object(b_cfg, "ADMIN_EMAILS", ["admin@helpusbr.com"]):
                            diag = b_cfg.validar_politica_seguranca_ambiente(enforce=False)
                            self.assertTrue(diag["conforme"])
                            self.assertEqual(len(diag["erros"]), 0)

        # 3. Desenvolvimento local com AUTH_REQUIRED=False é permitido sem erros
        with patch.object(b_cfg, "ENVIRONMENT", "development"):
            with patch.object(b_cfg, "AUTH_REQUIRED", False):
                diag = b_cfg.validar_politica_seguranca_ambiente(enforce=False)
                self.assertTrue(diag["conforme"])

    # --- Testes de Bloqueio Fail-Closed no Startup (Ordem 086) ---

    def test_startup_blocks_staging_when_auth_required_false_with_enforce(self):
        """Ordem 086: Bloqueio efetivo fail-closed no startup de staging se AUTH_REQUIRED for false."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "staging"):
            with patch.object(b_cfg, "AUTH_REQUIRED", False):
                with patch.dict("os.environ", {"ENVIRONMENT": "staging", "AUTH_REQUIRED": "false"}):
                    with self.assertRaises(RuntimeError) as ctx:
                        b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                    self.assertIn("AUTH_REQUIRED", str(ctx.exception))

    def test_startup_blocks_staging_when_reusing_production_client_id(self):
        """Ordem 086: Bloqueio efetivo em staging se tentar reutilizar o GOOGLE_CLIENT_ID de produção."""
        import backend.config as b_cfg
        prod_id = "812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com"
        with patch.object(b_cfg, "ENVIRONMENT", "staging"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.dict("os.environ", {"ENVIRONMENT": "staging", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": prod_id}):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", prod_id):
                        with self.assertRaises(RuntimeError) as ctx:
                            b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                        self.assertIn("reutilizar a credencial padrao de producao", str(ctx.exception))

    def test_startup_blocks_staging_when_client_id_missing_with_enforce(self):
        """Ordem 086: Bloqueio efetivo em staging se GOOGLE_CLIENT_ID estiver ausente."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "staging"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.dict("os.environ", {"ENVIRONMENT": "staging", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": ""}):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", ""):
                        with self.assertRaises(RuntimeError) as ctx:
                            b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                        self.assertIn("GOOGLE_CLIENT_ID ausente", str(ctx.exception))

    def test_startup_blocks_production_when_auth_required_false_with_enforce(self):
        """Ordem 086: Bloqueio efetivo fail-closed no startup de producao se AUTH_REQUIRED for false."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "production"):
            with patch.object(b_cfg, "AUTH_REQUIRED", False):
                with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "false"}):
                    with self.assertRaises(RuntimeError) as ctx:
                        b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                    self.assertIn("AUTH_REQUIRED", str(ctx.exception))

    def test_startup_development_mode_runs_cleanly_with_enforce(self):
        """Ordem 086: Em ambiente de desenvolvimento local, enforce=True não lança erro."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "development"):
            with patch.object(b_cfg, "AUTH_REQUIRED", False):
                with patch.dict("os.environ", {"ENVIRONMENT": "development", "AUTH_REQUIRED": "false"}):
                    diag = b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                    self.assertTrue(diag["conforme"])

    def test_backend_admin_ignores_client_tampering_of_next_public_admin_emails(self):
        """Ordem 086: O backend valida a autorização exclusivamente a partir de ADMIN_EMAILS do servidor.
        Qualquer manipulação do frontend (ex: NEXT_PUBLIC_ADMIN_EMAILS) não concede acesso."""
        import asyncio
        valid_user_payload = {
            "iss": "https://accounts.google.com",
            "sub": "sub_attacker_trying_frontend_bypass",
            "email": "attacker@helpusbr.com",
            "email_verified": True,
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=valid_user_payload):
            with patch.object(auth_backend, "GOOGLE_CLIENT_ID", self.mock_client_id):
                with patch.object(auth_backend, "ADMIN_EMAILS", ["realadmin@helpusbr.com"]):
                    with self.assertRaises(HTTPException) as ctx:
                        asyncio.run(auth_backend.obter_admin_google("Bearer attacker.token.sig"))
                    self.assertEqual(ctx.exception.status_code, 403)
                    self.assertEqual(ctx.exception.detail.get("error"), "admin_forbidden")

    # --- Testes de Configuração Explícita e Lifespan FastAPI Real (Ordem 087) ---

    def test_startup_blocks_production_when_client_id_not_explicitly_configured(self):
        """Ordem 087: Produção sem GOOGLE_CLIENT_ID configurado explicitamente no ambiente
        (recorrendo apenas ao fallback de código) DEVE falhar fail-closed com RuntimeError."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "production"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.object(b_cfg, "GOOGLE_CLIENT_ID", b_cfg.GOOGLE_CLIENT_ID_DEFAULT):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID_CONFIGURED_EXPLICITLY", False):
                        with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": ""}):
                            with self.assertRaises(RuntimeError) as ctx:
                                b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                            self.assertIn("GOOGLE_CLIENT_ID nao foi configurado explicitamente", str(ctx.exception))

    def test_startup_allows_production_when_client_id_is_explicitly_configured(self):
        """Ordem 087: Produção com GOOGLE_CLIENT_ID explicitamente declarado via variável de ambiente é aceito."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "production"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": "812202824664-prod.apps.googleusercontent.com"}):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", "812202824664-prod.apps.googleusercontent.com"):
                        with patch.object(b_cfg, "ADMIN_EMAILS", ["admin@helpusbr.com"]):
                            diag = b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                            self.assertTrue(diag["conforme"])
                            self.assertTrue(diag["google_client_id_explicit"])

    def test_startup_blocks_staging_when_client_id_not_explicitly_configured(self):
        """Ordem 087/088: Staging sem GOOGLE_CLIENT_ID configurado explicitamente deve falhar fail-closed."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "staging"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.object(b_cfg, "GOOGLE_CLIENT_ID", b_cfg.GOOGLE_CLIENT_ID_DEFAULT):
                    with patch.dict("os.environ", {"ENVIRONMENT": "staging", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": ""}):
                        with self.assertRaises(RuntimeError) as ctx:
                            b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                        self.assertTrue(
                            any(term in str(ctx.exception) for term in ["reutilizar a credencial padrao", "nao foi configurado explicitamente", "ausente"])
                        )

    # --- Testes de Endurecimento da Origem e Aliases de Deploy (Ordem 088) ---

    def test_in_memory_client_id_alteration_without_env_var_rejected_in_production(self):
        """Ordem 088: Alteração de GOOGLE_CLIENT_ID exclusivamente em memória sem variável de ambiente
        DEVE falhar fail-closed em produção, garantindo uma única fonte de verdade."""
        import backend.config as b_cfg
        with patch.object(b_cfg, "ENVIRONMENT", "production"):
            with patch.object(b_cfg, "AUTH_REQUIRED", True):
                with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "true"}, clear=True):
                    # Simula adulteração puramente no atributo do módulo em memória
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", "arbitrary-tampered-in-memory-client-id"):
                        with self.assertRaises(RuntimeError) as ctx:
                            b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                        self.assertIn("alteracao exclusiva em memoria e terminantemente proibido", str(ctx.exception))

    def test_production_alias_prod_enforces_strict_fail_closed_on_auth_required(self):
        """Ordem 088: Alias de produção 'prod' é reconhecido como ambiente protegido e exige AUTH_REQUIRED=true."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"ENVIRONMENT": "prod", "AUTH_REQUIRED": "false"}):
            with patch.object(b_cfg, "ENVIRONMENT", "prod"):
                with patch.object(b_cfg, "AUTH_REQUIRED", False):
                    with self.assertRaises(RuntimeError) as ctx:
                        b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                    self.assertIn("AUTH_REQUIRED deve ser estritamente True em ambiente protegido (prod)", str(ctx.exception))

    def test_production_alias_prod_rejects_missing_or_in_memory_client_id(self):
        """Ordem 088: Alias 'prod' rejeita GOOGLE_CLIENT_ID não declarado explicitamente no ambiente."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"ENVIRONMENT": "prod", "AUTH_REQUIRED": "true"}, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", "prod"):
                with patch.object(b_cfg, "AUTH_REQUIRED", True):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", b_cfg.GOOGLE_CLIENT_ID_DEFAULT):
                        with self.assertRaises(RuntimeError) as ctx:
                            b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                        self.assertIn("GOOGLE_CLIENT_ID nao foi configurado explicitamente via variavel de ambiente em prod", str(ctx.exception))

    def test_deploy_context_with_unknown_environment_fails_closed(self):
        """Ordem 088: Em contexto de deploy cloud (ex: Vercel=1), ambiente desconhecido/não-homologado é rejeitado."""
        import backend.config as b_cfg
        deploy_env = {
            "VERCEL": "1",
            "ENVIRONMENT": "corporate_intranet_preview",
            "AUTH_REQUIRED": "true",
            "GOOGLE_CLIENT_ID": "staging-dedicated-id.apps.googleusercontent.com"
        }
        with patch.dict("os.environ", deploy_env):
            with patch.object(b_cfg, "ENVIRONMENT", "corporate_intranet_preview"):
                with self.assertRaises(RuntimeError) as ctx:
                    b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                self.assertIn("Ambiente nao homologado 'corporate_intranet_preview' em contexto de deploy", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_in_memory_alteration_on_testclient(self):
        """Ordem 088: Ciclo de vida real via TestClient aborta se GOOGLE_CLIENT_ID foi alterado apenas em memória."""
        import backend.main as b_main
        with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "true"}, clear=True):
            with patch.object(b_main.app_config, "ENVIRONMENT", "production"):
                with patch.object(b_main.app_config, "AUTH_REQUIRED", True):
                    with patch.object(b_main.app_config, "GOOGLE_CLIENT_ID", "tampered-client-id-in-memory"):
                        with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                            with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                                with self.assertRaises(RuntimeError) as ctx:
                                    with TestClient(b_main.app):
                                        pass
                                self.assertIn("alteracao exclusiva em memoria", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_unknown_deploy_env_on_testclient(self):
        """Ordem 088: Ciclo de vida real via TestClient aborta se contexto de deploy carregar ambiente desconhecido."""
        import backend.main as b_main
        with patch.dict("os.environ", {"VERCEL": "1", "ENVIRONMENT": "unapproved_custom_env"}):
            with patch.object(b_main.app_config, "ENVIRONMENT", "unapproved_custom_env"):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(b_main.app):
                                pass
                        self.assertIn("Ambiente nao homologado", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_prod_alias_insecure_on_testclient(self):
        """Ordem 088: Ciclo de vida real via TestClient aborta se alias 'prod' tiver AUTH_REQUIRED=false."""
        import backend.main as b_main
        with patch.dict("os.environ", {"ENVIRONMENT": "prod", "AUTH_REQUIRED": "false"}):
            with patch.object(b_main.app_config, "ENVIRONMENT", "prod"):
                with patch.object(b_main.app_config, "AUTH_REQUIRED", False):
                    with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                        with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                            with self.assertRaises(RuntimeError) as ctx:
                                with TestClient(b_main.app):
                                    pass
                            self.assertIn("AUTH_REQUIRED", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_staging_when_auth_required_false_on_testclient(self):
        """Ordem 087: Execução do ciclo de vida FastAPI real via TestClient aborta startup em staging se AUTH_REQUIRED=false."""
        import backend.main as b_main
        with patch.object(b_main.app_config, "ENVIRONMENT", "staging"):
            with patch.object(b_main.app_config, "AUTH_REQUIRED", False):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(b_main.app):
                                pass
                        self.assertIn("AUTH_REQUIRED", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_staging_reusing_production_client_id_on_testclient(self):
        """Ordem 087: Ciclo de vida real do FastAPI aborta startup em staging se reutilizar Client ID de produção."""
        import backend.main as b_main
        prod_id = "812202824664-pm1o5qt84f3dsi3al0s6419oc3utt82g.apps.googleusercontent.com"
        with patch.object(b_main.app_config, "ENVIRONMENT", "staging"):
            with patch.object(b_main.app_config, "AUTH_REQUIRED", True):
                with patch.object(b_main.app_config, "GOOGLE_CLIENT_ID", prod_id):
                    with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                        with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                            with self.assertRaises(RuntimeError) as ctx:
                                with TestClient(b_main.app):
                                    pass
                            self.assertIn("reutilizar a credencial padrao de producao", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_production_without_explicit_client_id_on_testclient(self):
        """Ordem 087: Ciclo de vida real do FastAPI aborta startup em produção se GOOGLE_CLIENT_ID não for explícito."""
        import backend.main as b_main
        with patch.object(b_main.app_config, "ENVIRONMENT", "production"):
            with patch.object(b_main.app_config, "AUTH_REQUIRED", True):
                with patch.object(b_main.app_config, "GOOGLE_CLIENT_ID", b_main.app_config.GOOGLE_CLIENT_ID_DEFAULT):
                    with patch.object(b_main.app_config, "GOOGLE_CLIENT_ID_CONFIGURED_EXPLICITLY", False):
                        with patch.dict("os.environ", {"ENVIRONMENT": "production", "AUTH_REQUIRED": "true", "GOOGLE_CLIENT_ID": ""}):
                            with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                                with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                                    with self.assertRaises(RuntimeError) as ctx:
                                        with TestClient(b_main.app):
                                            pass
                                    self.assertIn("GOOGLE_CLIENT_ID nao foi configurado explicitamente", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_development_runs_cleanly_on_testclient(self):
        """Ordem 087: Ciclo de vida real do FastAPI inicia perfeitamente em modo de desenvolvimento local e responde requisições."""
        import backend.main as b_main
        with patch.object(b_main.app_config, "ENVIRONMENT", "development"):
            with patch.object(b_main.app_config, "AUTH_REQUIRED", False):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with TestClient(b_main.app) as client:
                            resp = client.get("/saude")
                            self.assertEqual(resp.status_code, 200)
                            self.assertEqual(resp.json().get("status"), "saudavel")

    def test_fastapi_lifespan_lifecycle_mirror_api_main_on_testclient(self):
        """Ordem 087: Espelho api/main.py também executa o ciclo de vida real com fail-closed idêntico."""
        ROOT = Path(__file__).resolve().parents[1]
        if str(ROOT / "api") not in sys.path:
            sys.path.insert(0, str(ROOT / "api"))
        import api.main as a_main
        with patch.object(a_main.app_config, "ENVIRONMENT", "staging"):
            with patch.object(a_main.app_config, "AUTH_REQUIRED", False):
                with patch.object(a_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(a_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(a_main.app):
                                pass
                        self.assertIn("AUTH_REQUIRED", str(ctx.exception))

    # --- Testes de Deploy Environment Gate e Salvaguardas Serverless (Ordem 089) ---

    def test_deploy_context_vercel_blocks_development_environment(self):
        """Ordem 089: VERCEL=1 com ENVIRONMENT=development DEVE falhar fail-closed com RuntimeError."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"VERCEL": "1", "ENVIRONMENT": "development", "AUTH_REQUIRED": "false"}, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", "development"):
                with self.assertRaises(RuntimeError) as ctx:
                    b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                self.assertIn("Ambiente de desenvolvimento 'development' e terminantemente proibido em contexto de deploy cloud", str(ctx.exception))

    def test_deploy_context_blocks_missing_environment(self):
        """Ordem 089: VERCEL definido com ENVIRONMENT ausente ou vazio DEVE falhar fail-closed."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"VERCEL": "", "ENVIRONMENT": ""}, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", ""):
                with self.assertRaises(RuntimeError) as ctx:
                    b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                self.assertIn("ENVIRONMENT ausente ou vazio em contexto de deploy cloud", str(ctx.exception))

    def test_deploy_context_railway_blocks_dev_alias(self):
        """Ordem 089: RAILWAY_ENVIRONMENT com ENVIRONMENT=dev DEVE falhar fail-closed."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"RAILWAY_ENVIRONMENT": "dev", "ENVIRONMENT": "dev"}, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", "dev"):
                with self.assertRaises(RuntimeError) as ctx:
                    b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                self.assertIn("Ambiente de desenvolvimento 'dev' e terminantemente proibido", str(ctx.exception))

    def test_deploy_context_allows_valid_staging_with_explicit_credentials(self):
        """Ordem 089: Deploy cloud em staging com AUTH_REQUIRED=true e GOOGLE_CLIENT_ID dedicado é aceito."""
        import backend.config as b_cfg
        staging_env = {
            "VERCEL": "1",
            "ENVIRONMENT": "staging",
            "AUTH_REQUIRED": "true",
            "GOOGLE_CLIENT_ID": "staging-dedicated-id-1234.apps.googleusercontent.com",
            "ADMIN_EMAILS": "admin@helpusbr.com",
        }
        with patch.dict("os.environ", staging_env, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", "staging"):
                with patch.object(b_cfg, "AUTH_REQUIRED", True):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", staging_env["GOOGLE_CLIENT_ID"]):
                        with patch.object(b_cfg, "ADMIN_EMAILS", ["admin@helpusbr.com"]):
                            diag = b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                            self.assertTrue(diag["conforme"])
                            self.assertTrue(diag["is_deploy_context"])
                            self.assertTrue(diag["is_protected"])

    def test_deploy_context_allows_valid_production_with_explicit_credentials(self):
        """Ordem 089: Deploy cloud em production com AUTH_REQUIRED=true e GOOGLE_CLIENT_ID explícito é aceito."""
        import backend.config as b_cfg
        prod_env = {
            "RAILWAY_ENVIRONMENT": "production",
            "ENVIRONMENT": "production",
            "AUTH_REQUIRED": "true",
            "GOOGLE_CLIENT_ID": "812202824664-prod-explicit.apps.googleusercontent.com",
            "ADMIN_EMAILS": "admin@helpusbr.com",
        }
        with patch.dict("os.environ", prod_env, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", "production"):
                with patch.object(b_cfg, "AUTH_REQUIRED", True):
                    with patch.object(b_cfg, "GOOGLE_CLIENT_ID", prod_env["GOOGLE_CLIENT_ID"]):
                        with patch.object(b_cfg, "ADMIN_EMAILS", ["admin@helpusbr.com"]):
                            diag = b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                            self.assertTrue(diag["conforme"])
                            self.assertTrue(diag["is_deploy_context"])
                            self.assertTrue(diag["is_protected"])

    def test_fastapi_lifespan_lifecycle_blocks_deploy_with_development_on_testclient(self):
        """Ordem 089: Ciclo de vida real via TestClient aborta se deploy carregar ENVIRONMENT=development."""
        import backend.main as b_main
        with patch.dict("os.environ", {"VERCEL": "1", "ENVIRONMENT": "development", "AUTH_REQUIRED": "false"}, clear=True):
            with patch.object(b_main.app_config, "ENVIRONMENT", "development"):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(b_main.app):
                                pass
                        self.assertIn("Ambiente de desenvolvimento 'development' e terminantemente proibido", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_deploy_missing_environment_on_testclient(self):
        """Ordem 089: Ciclo de vida real via TestClient aborta se deploy omitir ENVIRONMENT."""
        import backend.main as b_main
        with patch.dict("os.environ", {"VERCEL": "1", "ENVIRONMENT": ""}, clear=True):
            with patch.object(b_main.app_config, "ENVIRONMENT", ""):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(b_main.app):
                                pass
                        self.assertIn("ENVIRONMENT ausente ou vazio em contexto de deploy", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_allows_deploy_staging_on_testclient(self):
        """Ordem 089: Ciclo de vida real via TestClient inicia perfeitamente em staging cloud válido e serve requisições."""
        import backend.main as b_main
        staging_env = {
            "VERCEL": "1",
            "ENVIRONMENT": "staging",
            "AUTH_REQUIRED": "true",
            "GOOGLE_CLIENT_ID": "staging-dedicated-testclient-1234.apps.googleusercontent.com",
            "ADMIN_EMAILS": "admin@helpusbr.com",
        }
        with patch.dict("os.environ", staging_env, clear=True):
            with patch.object(b_main.app_config, "ENVIRONMENT", "staging"):
                with patch.object(b_main.app_config, "AUTH_REQUIRED", True):
                    with patch.object(b_main.app_config, "GOOGLE_CLIENT_ID", staging_env["GOOGLE_CLIENT_ID"]):
                        with patch.object(b_main.app_config, "ADMIN_EMAILS", ["admin@helpusbr.com"]):
                            with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                                with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                                    with TestClient(b_main.app) as client:
                                        resp = client.get("/saude")
                                        self.assertEqual(resp.status_code, 200)
                                        self.assertEqual(resp.json().get("status"), "saudavel")

    # --- Testes de Fechamento do Gate e Alinhamento de Credenciais (Ordem 090) ---

    def test_deploy_context_blocks_missing_env_even_with_staging_in_module_memory(self):
        """Ordem 090: VERCEL=1 com ENVIRONMENT ausente no lookup DEVE abortar com erro,
        mesmo que o atributo b_cfg.ENVIRONMENT em memória tenha 'staging'."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"VERCEL": "1"}, clear=True):
            # Injeta em memória no módulo, simulando atributo em cache
            with patch.object(b_cfg, "ENVIRONMENT", "staging"):
                with self.assertRaises(RuntimeError) as ctx:
                    b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                self.assertIn("ENVIRONMENT ausente ou vazio em contexto de deploy cloud", str(ctx.exception))

    def test_deploy_context_blocks_missing_env_even_with_prod_in_module_memory(self):
        """Ordem 090: VERCEL=1 com ENVIRONMENT ausente no lookup DEVE abortar com erro,
        mesmo que o atributo b_cfg.ENVIRONMENT em memória tenha 'production' ou 'prod'."""
        import backend.config as b_cfg
        with patch.dict("os.environ", {"VERCEL": "1", "ENVIRONMENT": ""}, clear=True):
            with patch.object(b_cfg, "ENVIRONMENT", "production"):
                with self.assertRaises(RuntimeError) as ctx:
                    b_cfg.validar_politica_seguranca_ambiente(enforce=True)
                self.assertIn("ENVIRONMENT ausente ou vazio em contexto de deploy cloud", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_deploy_missing_env_despite_module_staging_on_testclient(self):
        """Ordem 090: Ciclo de vida real via TestClient aborta se deploy cloud omitir ENVIRONMENT,
        mesmo que o app_config em memória tenha sido patcheado com 'staging'."""
        import backend.main as b_main
        with patch.dict("os.environ", {"VERCEL": "1"}, clear=True):
            with patch.object(b_main.app_config, "ENVIRONMENT", "staging"):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(b_main.app):
                                pass
                        self.assertIn("ENVIRONMENT ausente ou vazio em contexto de deploy cloud", str(ctx.exception))

    def test_fastapi_lifespan_lifecycle_blocks_deploy_missing_env_despite_module_prod_on_testclient(self):
        """Ordem 090: Ciclo de vida real via TestClient aborta se deploy cloud omitir ENVIRONMENT,
        mesmo que o app_config em memória tenha sido patcheado com 'prod'."""
        import backend.main as b_main
        with patch.dict("os.environ", {"VERCEL": "1", "ENVIRONMENT": "   "}, clear=True):
            with patch.object(b_main.app_config, "ENVIRONMENT", "prod"):
                with patch.object(b_main.banco, "conectar", new_callable=AsyncMock):
                    with patch.object(b_main.banco, "criar_tabelas", new_callable=AsyncMock):
                        with self.assertRaises(RuntimeError) as ctx:
                            with TestClient(b_main.app):
                                pass
                        self.assertIn("ENVIRONMENT ausente ou vazio em contexto de deploy cloud", str(ctx.exception))

    def test_auth_verificar_google_id_token_strictly_uses_os_environ_client_id(self):
        """Ordem 090: Confirma que verificar_google_id_token utiliza estritamente o GOOGLE_CLIENT_ID
        configurado na variável de ambiente do SO, garantindo alinhamento total entre startup e request."""
        expected_client_id = "staging-client-from-os-environ.apps.googleusercontent.com"
        token = "dummy.token.here"
        mock_payload = {
            "iss": "https://accounts.google.com",
            "sub": "user_123",
            "email": "user@helpusbr.com",
            "email_verified": True,
        }
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": expected_client_id}):
            with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_payload) as mock_verify:
                profile = auth_backend.verificar_google_id_token(token)
                self.assertEqual(profile["email"], "user@helpusbr.com")
                # Confirma que verify_oauth2_token recebeu exatamente o Client ID da variável de ambiente
                mock_verify.assert_called_once()
                args, kwargs = mock_verify.call_args
                self.assertEqual(args[2], expected_client_id)


if __name__ == "__main__":
    unittest.main()
