# -*- coding: utf-8 -*-
import os
from typing import Optional, Dict, Any

from fastapi import Header, HTTPException

from config import AUTH_REQUIRED, GOOGLE_CLIENT_ID, ADMIN_EMAILS


def verificar_google_id_token(token: str) -> Dict[str, Any]:
    if not token or not isinstance(token, str) or not token.strip():
        raise HTTPException(
            status_code=401,
            detail={"error": "missing_google_token", "message": "Token ausente ou invalido. Faca login novamente."},
        )

    # Alinhamento estrito com o startup: prioriza a variavel de ambiente do SO (fonte unica em deploy)
    env_id = os.getenv("GOOGLE_CLIENT_ID")
    if env_id is not None and env_id.strip():
        client_id = env_id.strip()
    else:
        client_id = (GOOGLE_CLIENT_ID or "").strip()
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail={"error": "oauth_configuration_error", "message": "Google Client ID nao configurado."},
        )

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests

        # verify_oauth2_token valida rigorosamente:
        # 1. Assinatura criptográfica com chaves públicas do Google (Google certs)
        # 2. Expiração do token (exp)
        # 3. Audiência (aud == GOOGLE_CLIENT_ID)
        # 4. Emissor (iss in accounts.google.com / https://accounts.google.com)
        info = id_token.verify_oauth2_token(
            token.strip(),
            requests.Request(),
            client_id,
        )
    except Exception:
        # FAIL-CLOSED: Qualquer falha na verificação criptográfica, expiração, audiência
        # ou emissor rejeita a requisição imediatamente com 401.
        # NUNCA decodificar sem verificar assinatura. NUNCA logar tokens ou segredos.
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_google_token", "message": "Sessao expirada ou invalida. Faca login novamente."},
        ) from None

    if not info or not isinstance(info, dict):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_google_token", "message": "Payload do token Google invalido."},
        )

    # Verificação fail-closed adicional de emissor
    iss = info.get("iss")
    if iss not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_google_token", "message": "Emissor (iss) do token Google invalido."},
        )

    # Validar sub (Subject identifier)
    sub = info.get("sub")
    if not sub or not isinstance(sub, str) or not sub.strip():
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_google_token", "message": "Token Google sem sub valido."},
        )

    # Validar email
    email = info.get("email")
    if not email or not isinstance(email, str) or not email.strip():
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_google_token", "message": "Token Google sem email. Faca login novamente."},
        )

    # Validar email_verified: exigir estritamente o booleano True (rejeita None, "true", "false", 0, False ou ausente)
    if info.get("email_verified") is not True:
        raise HTTPException(
            status_code=401,
            detail={"error": "unverified_email", "message": "Email Google nao verificado pelo provedor."},
        )

    return {
        "sub": sub.strip(),
        "email": email.strip().lower(),
        "name": info.get("name") or email.strip().lower(),
        "picture": info.get("picture") or "",
    }


async def obter_usuario_google(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token and token.lower() not in ("null", "undefined", "none", ""):
            return verificar_google_id_token(token)

    if AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail={"error": "auth_required", "message": "Login Google obrigatorio."})

    return None


async def obter_admin_google(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"error": "auth_required", "message": "Login Google obrigatorio."})

    token = authorization.split(" ", 1)[1].strip()
    if not token or token.lower() in ("null", "undefined", "none"):
        raise HTTPException(status_code=401, detail={"error": "missing_google_token", "message": "Token ausente. Faca login novamente."})

    usuario = verificar_google_id_token(token)
    email = str(usuario.get("email") or "").lower()
    if not ADMIN_EMAILS or email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail={"error": "admin_forbidden", "message": "Conta sem permissao de admin."})
    return usuario
