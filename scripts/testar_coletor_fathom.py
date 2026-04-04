import sys
import logging
from pathlib import Path

# Setup Project Path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.fathom_service import sync_fathom_data

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=== NSS LISTEN: TESTANDO COLETOR FATHOM ===")
    print("[*] Iniciando sincronização simulada de chamadas...")
    
    try:
        sync_fathom_data()
        print("\n[✔] Sincronização Fathom concluída com sucesso!")
        print("[TIP] Verifique a aba 'db_fathom' no seu SSoT ou logs do Redis.")
        
    except Exception as e:
        logger.error(f"[X] Erro no coletor Fathom: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
