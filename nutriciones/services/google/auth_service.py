from pathlib import Path
import logging
from typing import Any, Literal
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCreds
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from nutriciones.core import config

logger = logging.getLogger(__name__)

# Scopes updated to include both Rebirth's needs and current project's needs (docs, sheets, drive)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents'
]

import json
import redis
from google_auth_oauthlib.flow import Flow
from nutriciones.services.google.sheets.indices import get_indices

logger = logging.getLogger(__name__)

# Scopes updated to include both Rebirth's needs and current project's needs (docs, sheets, drive)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents'
]

_creds = None

def _get_redis():
    indices = get_indices()
    return indices.redis_client

def get_creds() -> OAuthCreds:
    global _creds
    if _creds: return _creds

    creds = None
    token_data = None
    
    # 1. Tentar carregar do Redis (Stateless - Fator VI)
    r = _get_redis()
    if r:
        token_json = r.get("nss:google:token")
        if token_json:
            logger.info("[✔] Token Google recuperado do Redis.")
            token_data = json.loads(token_json)
            creds = OAuthCreds.from_authorized_user_info(token_data, SCOPES)
        else:
            logger.warning("[!] Chave 'nss:google:token' NÃO encontrada no Redis.")

    # 2. Fallback para token.json local
    if not creds:
        token_path = config.BASE_DIR / 'token.json'
        if token_path.exists():
            logger.info("[✔] Token Google carregado de arquivo local.")
            creds = OAuthCreds.from_authorized_user_info(json.loads(token_path.read_text()), SCOPES)

    if creds:
        if not creds.expired:
            _creds = creds
            return creds
        elif creds.refresh_token:
            try:
                logger.info("[*] Token expirado. Tentando refresh...")
                creds.refresh(Request())
                _creds = creds
                # Atualizar Redis após refresh
                if r:
                    r.set("nss:google:token", creds.to_json())
                logger.info("[✔] Token Google atualizado com Refresh Token.")
                return creds
            except Exception as e:
                logger.warning(f"[X] Erro no refresh: {e}")

    logger.warning("[!] Nenhuma credencial Google ativa. Onboarding necessário.")
    return None

def get_auth_flow(redirect_uri: str) -> Flow:
    """Gera o flow para o processo de Onboarding Web."""
    credentials_path = config.BASE_DIR / 'credentials.json'
    if not credentials_path.exists():
        raise FileNotFoundError(f"Coloque seu credentials.json em {config.BASE_DIR}")
        
    return Flow.from_client_secrets_file(
        str(credentials_path),
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def save_token(token_json: str):
    """Persiste o token no Redis e localmente."""
    global _creds
    _creds = OAuthCreds.from_authorized_user_info(json.loads(token_json), SCOPES)
    
    # SSalva no Redis
    r = _get_redis()
    if r:
        r.set("nss:google:token", token_json)
        logger.info("Token persistido no Redis com sucesso.")
        
    # Backup local
    token_path = config.BASE_DIR / 'token.json'
    token_path.write_text(token_json)
    logger.info("Token persistido no token.json local.")

def get_ssot_sheets_service():
    """Retorna o client (service) da API do Google Sheets (v4) autenticado."""
    creds = get_creds()
    if not creds:
        logger.error("[!] Não é possível criar o serviço do Google Sheets: Credenciais ausentes.")
        return None
    try:
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        logger.error(f"[X] Falha ao construir o serviço do Google: {e}")
        return None

def get_drive_service():
    """Retorna o client (service) da API do Google Drive (v3) autenticado."""
    creds = get_creds()
    return build('drive', 'v3', credentials=creds)

def get_docs_service():
    """Retorna o client (service) da API do Google Docs (v1) autenticado."""
    creds = get_creds()
    return build('docs', 'v1', credentials=creds)
