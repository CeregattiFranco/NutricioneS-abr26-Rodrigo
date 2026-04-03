import os
import logging
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuração simples de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura o escopo expansivo para múltiplas APIs do Google
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

def get_service_account_creds() -> service_account.Credentials:
    """
    Carrega as variáveis do .env e retorna as credenciais da Service Account.
    """
    # Carrega as variáveis do arquivo .env
    load_dotenv()
    
    email = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')
    private_key = os.getenv('GOOGLE_PRIVATE_KEY')
    
    if not email or not private_key:
        logger.error("Credenciais da Service Account não encontradas no arquivo .env.")
        raise ValueError("Variáveis GOOGLE_SERVICE_ACCOUNT_EMAIL ou GOOGLE_PRIVATE_KEY ausentes.")
    
    # Tratamento da chave privada que pode ter as quebras de linha escapadas
    private_key = private_key.replace('\\n', '\n')
    
    # Cria o dicionário mínimo necessário para autenticação
    info = {
        'client_email': email,
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
