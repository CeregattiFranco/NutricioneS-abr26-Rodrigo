import sys
import logging
from pathlib import Path

# Setup Project Path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.digest import gerar_digest_diario

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=== NSS SABLA: INICIANDO GERAÇÃO DE DIGEST DIÁRIO ===")
    print("[*] Cruzando dados de Consultas, Prontuários e E-mails...")
    
    try:
        report = gerar_digest_diario()
        print("\n[✔] Digest Diário gerado e enviado com sucesso!")
        print("\n=== CONTEÚDO DO RELATÓRIO ===")
        print(report)
        print("================================")
    except Exception as e:
        logger.error(f"[X] Erro ao gerar Digest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
