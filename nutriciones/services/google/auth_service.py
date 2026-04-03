import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

from nutriciones.core import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

def get_service_account_creds() -> service_account.Credentials:
    """
    Carrega as variáveis do config e retorna as credenciais da Service Account.
    """
    private_key = config.GOOGLE_PRIVATE_KEY.replace('\\n', '\n')
    
    info = {
        'client_email': config.GOOGLE_SERVICE_ACCOUNT_EMAIL,
        'private_key': private_key,
        'token_uri': 'https://oauth2.googleapis.com/token'
    }
    
    try:
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=SCOPES
        )
        logger.info("Credenciais da Service Account carregadas com sucesso.")
        return creds
    except Exception as e:
        logger.error(f"Erro ao gerar credenciais da Service Account: {e}")
        raise

def get_ssot_sheets_service():
    """
    Retorna o client (service) da API do Google Sheets (v4) autenticado.
    """
    creds = get_service_account_creds()
    try:
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Erro ao inicializar o serviço do Google Sheets: {e}")
        raise

def get_drive_service():
    """
    Retorna o client (service) da API do Google Drive (v3) autenticado.
    """
    creds = get_service_account_creds()
    try:
        service = build('drive', 'v3', credentials=creds)
        logger.info("Serviço do Google Drive v3 inicializado com sucesso.")
        return service
    except Exception as e:
        logger.error(f"Erro ao inicializar o serviço do Google Drive: {e}")
        raise

def get_docs_service():
    """
    Retorna o client (service) da API do Google Docs (v1) autenticado.
    """
    creds = get_service_account_creds()
    try:
        service = build('docs', 'v1', credentials=creds)
        logger.info("Serviço do Google Docs v1 inicializado com sucesso.")
        return service
    except Exception as e:
        logger.error(f"Erro ao inicializar o serviço do Google Docs: {e}")
        raise
