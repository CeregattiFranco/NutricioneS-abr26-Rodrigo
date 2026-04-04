import os
import sys

# Adicionar o diretório raiz ao path para permitir importações do módulo nutriciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nutriciones.services.fathom_service import sync_fathom_data
from nutriciones.core import get_base_logger

logger = get_base_logger("NSS-FATHOM-SCRIPT")

if __name__ == "__main__":
    logger.info("Executando sincronização manual do Fathom AI...")
    try:
        sync_fathom_data()
        logger.info("Script finalizado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao executar script: {e}")
        sys.exit(1)
