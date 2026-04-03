import sys
from pathlib import Path

# Padrão PathLib Rebirth
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

from nutriciones.core import config
from nutriciones.services.google.auth_service import get_ssot_sheets_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def testar_conexao_oauth():
    try:
        logger.info("Iniciando Validação de Conexão OAuth2 (Rebirth)...")
        service = get_ssot_sheets_service()
        
        spreadsheet_id = config.GoogleServices.sheet_id_cardapio
        range_name = 'db_alimentos!A1:Z1'
        
        logger.info(f"Tentando ler cabeçalhos ({range_name}) da Planilha...")
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, 
            range=range_name
        ).execute()
        
        headers = result.get('values', [])
        
        if not headers:
            logger.warning("Conexão OK, mas sem cabeçalhos encontrados na aba db_alimentos.")
        else:
            logger.info("Sucesso! Cabeçalhos encontrados:")
            logger.info(f" -> {headers[0]}")
            
    except Exception as e:
        logger.error(f"Falha ao validar os tokens ou permissões: {e}")
        logger.error("Token.json local parece inválido ou faltam permissões.")

if __name__ == "__main__":
    testar_conexao_oauth()
