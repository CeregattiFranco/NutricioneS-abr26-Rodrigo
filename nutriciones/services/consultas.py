import uuid
import logging
from datetime import datetime, timedelta

from nutriciones.models.consultas import Consulta
from nutriciones.services.google.sheets.base import inserir_recurso
from nutriciones.services.google.sheets.types import PedidoInsercaoRecurso
from nutriciones.services.pacientes import generic_serializer
from nutriciones.services.google.calendar import criar_evento, NovoEvento

from nutriciones.core import config
from nutriciones.services.google.sheets.base import sheet_name_of_resource_type

logger = logging.getLogger(__name__)

def agendar_consulta(
    pct_id: str,
    agd_id: str,
    start: datetime = None,
    end: datetime = None
) -> dict:
    """
    Agiliza o vínculo do Paciente à Agenda gerando um evento na Google Calendar (com Meet),
    e armazena as chaves no banco de SSoT.
    """
    cns_id = uuid.uuid4().hex
    agora = datetime.now()
    
    # Defaults in case caller didn't provide dates to save a network fetch
    if not start:
        start = agora + timedelta(days=1)
    if not end:
        end = start + timedelta(hours=1)
    
    logger.info("Solicitando evento na Google Calendar com injeção do Meet...")
    calendar_id = config.GoogleServices.calendar_id or "primary"
    
    evento = NovoEvento(
        calendar_id=calendar_id,
        summary="Consulta Nutricional - NSS",
        description=f"Atendimento presencial/telemedicina automático gerado pelo sistema para {pct_id}",
        start=start,
        end=end
    )
    
    event_id, event_url, meet_url = criar_evento(evento)
    
    logger.info(f"Gerado o Google Meet: {meet_url}")
    
    consulta = Consulta(
        cns_id=cns_id,
        pct_id=pct_id,
        agd_id=agd_id,
        consulta_perfil="adulto",
        status="agendado",
        ativo=True,
        slot="primeira_vez",
        calendar_event_id=event_id,
        meet_url=meet_url,
        calendar_event_url=event_url,
        created_at=agora,
        updated_at=agora
    )
    
    logger.info("Persistindo matriz Consulta SSoT e Indices...")
    inserir_recurso(PedidoInsercaoRecurso(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Consulta],
        recurso=consulta,
        serialize=generic_serializer
    ))
    
    return {
        "cns_id": cns_id,
        "meet_url": meet_url,
        "event_id": event_id
    }
