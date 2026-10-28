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
from unittest.mock import patch, MagicMock

from fastapi import HTTPException

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


if __name__ == "__main__":
    unittest.main()
