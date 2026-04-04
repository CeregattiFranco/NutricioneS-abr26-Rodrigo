import sys
import logging
from pathlib import Path

# Setup Project Path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.backup_service import executar_backup_diario

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=== NSS SHIELD: TESTANDO DISASTER RECOVERY (BACKUP) ===")
    print("[*] Iniciando geração de pacote SSoT + DB...")
    
    try:
        executar_backup_diario()
        print("\n[✔] Backup local gerado com sucesso!")
        print("[TIP] Verifique o diretório 'backups/' na raiz do projeto.")
        
    except Exception as e:
        logger.error(f"[X] Erro no NSS Shield: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
