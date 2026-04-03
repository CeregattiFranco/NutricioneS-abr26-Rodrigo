import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, date, time

sys.path.insert(0, str(Path(__file__).parent.parent))

from nutriciones.services.agenda import criar_slot_agenda
from nutriciones.services.consultas import agendar_consulta
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.models.consultas import Consulta
from nutriciones.models.pacientes import Paciente

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    pct_id = "paciente-teste-123" # O paciente teste que já embarcamos e validamos antes
    if len(sys.argv) > 1:
        pct_id = sys.argv[1]
        
    logger.info("=== TESTE DE INTEGRAÇÃO: MÓDULO DE CONSULTA E AGENDA ===")

    # 1. Criação do Slot de Agenda (Disponibilidade do Nutricionista)
    agora = datetime.now()
    inicio_slot = (agora + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)
    fim_slot = inicio_slot + timedelta(hours=1)
    
    logger.info(f"Gerando slot de agenda para o dia {inicio_slot.strftime('%d/%m/%Y às %H:%M')}...")
    agd_id = criar_slot_agenda(
        data_slot=inicio_slot.date(),
        hora_inicio=inicio_slot.time(),
        hora_fim=fim_slot.time()
    )
    
    logger.info(f"Slot mapeado sob ID: {agd_id}")

    # 2. Transformando em Consulta Vinculada
    logger.info(f"Vinculando Paciente ({pct_id}) ao Slot ({agd_id})...")
    
    try:
        resultado = agendar_consulta(
            pct_id=pct_id,
            agd_id=agd_id,
            start=inicio_slot,
            end=fim_slot
        )
    except Exception as e:
        logger.error(f"Erro ao agendar consulta e se comunicar com o Calendar: {e}")
        return
        
    cns_id = resultado['cns_id']
    meet = resultado['meet_url']
    event = resultado['event_id']

    logger.info(f"[✔] Consulta criada com sucesso!")
    logger.info(f"Consulta ID: {cns_id}")
    logger.info(f"Google Calendar ID: {event}")
    logger.info(f"URL de Videoconferência Gerada: {meet}")
    
    # 3. Validar se alocou em O(1) no Cache
    logger.info("\n=== VERIFICANDO RESULTADOS NOS ÍNDICES (MEMÓRIA O(1)) ===")
    
    try:
        indices = get_indices()
    except Exception as e:
        logger.error(f"Não foi possível carregar os índices: {e}")
        return
        
    b_refs = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key=pct_id,
        primary_sheet=Consulta
    )
    
    if cns_id in b_refs:
        logger.info(f"[✔] Sincronização Perfeita: Consulta {cns_id} está referenciando o Paciente {pct_id} no arquivo de memória O(1).")
    else:
        logger.warning(f"[X] Avisou O(1) fail. A consulta persistiu na Cloud mas o cache local não viu {cns_id} como back reference.")


if __name__ == "__main__":
    main()
