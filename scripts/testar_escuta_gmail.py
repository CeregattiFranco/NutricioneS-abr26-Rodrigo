import sys
import logging
from pathlib import Path

# Setup Project Path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.google.gmail_listener import listen_gmail_inbox

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=== MORDOMO DE E-MAILS: INICIANDO ESCUTA GMAIL ===")
    print("[*] Buscando mensagens is:unread de pacientes registrados...")
    
    try:
        listen_gmail_inbox()
        print("\n[✔] Ciclo de escuta concluído com sucesso!")
        print("[*] Verifique a aba 'db_mensagens' para ver os logs e resumos da IA.")
    except Exception as e:
        logger.error(f"[X] Falha crítica no Mordomo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
