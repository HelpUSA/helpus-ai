# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any

from fastapi import Header, HTTPException

from config import AUTH_REQUIRED, GOOGLE_CLIENT_ID, ADMIN_EMAILS


def verificar_google_id_token(token: str) -> Dict[str, Any]:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID nao configurado.")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests

        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "invalid_google_token", "message": "Sessao expirada ou invalida. Faca login novamente."})

    email = info.get("email")
    if not email:
        raise HTTPException(status_code=401, detail={"error": "invalid_google_token", "message": "Token Google sem email. Faca login novamente."})

    return {
        "sub": info.get("sub"),
        "email": email,
        "name": info.get("name") or email,
        "picture": info.get("picture") or "",
    }


async def obter_usuario_google(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    if not AUTH_REQUIRED:
        return None

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"error": "auth_required", "message": "Login Google obrigatorio."})

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail={"error": "missing_google_token", "message": "Token ausente. Faca login novamente."})

    return verificar_google_id_token(token)


async def obter_admin_google(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"error": "auth_required", "message": "Login Google obrigatorio."})

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail={"error": "missing_google_token", "message": "Token ausente. Faca login novamente."})

    usuario = verificar_google_id_token(token)
    email = str(usuario.get("email") or "").lower()
    if ADMIN_EMAILS and email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail={"error": "admin_forbidden", "message": "Conta sem permissao de admin."})
    return usuario
