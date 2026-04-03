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

_creds = None

def get_creds() -> OAuthCreds:
    global _creds
    if _creds:
        return _creds

    creds = None
    token_path = config.BASE_DIR / 'token.json'
    credentials_path = config.BASE_DIR / 'credentials.json'

    if token_path.exists():
        creds = OAuthCreds.from_authorized_user_file(str(token_path), SCOPES)

    if creds:
        if not creds.expired:
            _creds = creds
            logger.info("Credenciais OAuth carregadas do token.json.")
            return creds
        elif creds.refresh_token:
            try:
                creds.refresh(Request())
                _creds = creds
                logger.info("Credenciais OAuth atualizadas (refresh).")
                return creds
            except Exception as e:
                logger.warning(f"Erro no refresh token: {e}")
                pass

    logger.info("Iniciando fluxo de autenticação OAuth...")
    if not credentials_path.exists():
        logger.error(f"Erro fatal de permissão/auth: {credentials_path} inacessível.")
        raise FileNotFoundError(f"Coloque seu credentials.json em {config.BASE_DIR}")
        
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, 'w') as token:
        token.write(creds.to_json())

    _creds = creds
    logger.info("Novas credenciais OAuth geradas e salvas em token.json.")
    return creds

def get_ssot_sheets_service():
    """Retorna o client (service) da API do Google Sheets (v4) autenticado."""
    creds = get_creds()
    return build('sheets', 'v4', credentials=creds)

def get_drive_service():
    """Retorna o client (service) da API do Google Drive (v3) autenticado."""
    creds = get_creds()
    return build('drive', 'v3', credentials=creds)

def get_docs_service():
    """Retorna o client (service) da API do Google Docs (v1) autenticado."""
    creds = get_creds()
    return build('docs', 'v1', credentials=creds)
