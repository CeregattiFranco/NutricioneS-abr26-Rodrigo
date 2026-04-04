import sys
import logging
from pathlib import Path

# Setup Project Path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.campanhas import processar_fila_mensagens
from nutriciones.services.confirmacoes import rodar_regua_confirmacao
from nutriciones.utils.telemetry import monitor_execution

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@monitor_execution
def main():
    print("=== NSS SABLA: INICIANDO TAREFAS DIÁRIAS (CRON) ===")
    
    # 1. Régua de Confirmação (Consultas Futuras)
    try:
        rodar_regua_confirmacao()
        print("[✔] Régua de confirmação executada com sucesso.")
    except Exception as e:
        logger.error(f"[X] Erro na régua de confirmação: {e}")
        
    # 2. Processar Mensagens Agendadas (Fila Educativa / Follow-up)
    try:
        processar_fila_mensagens()
        print("[✔] Fila de mensagens agendadas processada.")
    except Exception as e:
        logger.error(f"[X] Erro ao processar fila de mensagens: {e}")
        
    print("\n=== Ciclo Diário Finalizado no NSS. SSoT Sincronizada! ===")

if __name__ == "__main__":
    main()
