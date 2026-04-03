import sys
from pathlib import Path

# Padrão PathLib da Rebirth
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

from nutriciones.core import config
from nutriciones.services.google.auth_service import get_ssot_sheets_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def testar_conexao_completa():
    try:
        logger.info("Iniciando teste de conexão OAuth2 (Padrão Rebirth)...")
        
        # 1. Tenta inicializar o serviço (isso deve disparar o navegador se necessário)
        service = get_ssot_sheets_service()
        
        # 2. Tenta ler um range simples da planilha db_alimentos
        spreadsheet_id = config.GoogleServices.sheet_id_cardapio
        range_name = 'db_alimentos!A1:B10'
        
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, 
            range=range_name
        ).execute()
        
        values = result.get('values', [])

        if not values:
            logger.warning("Conexão OK, mas a aba 'db_alimentos' parece estar vazia.")
        else:
            logger.info(f"Sucesso! Conseguimos ler {len(values)} linhas da planilha.")
            for row in values[:3]: # Mostra as 3 primeiras linhas
                print(f" -> {row}")

        logger.info("Teste finalizado com sucesso. O arquivo 'token.json' deve ter sido gerado/atualizado.")

    except Exception as e:
        logger.error(f"Falha no teste de conexão: {e}")
        print("\n--- DICA DE RESOLUÇÃO ---")
        print("1. Certifique-se de que o arquivo 'credentials.json' está na raiz.")
        print("2. Verifique se o ID da planilha no seu .env está correto.")

if __name__ == "__main__":
    testar_conexao_completa()
