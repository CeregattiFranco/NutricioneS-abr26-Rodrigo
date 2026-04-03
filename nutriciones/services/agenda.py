import uuid
import logging
from datetime import date, time, datetime

from nutriciones.models.agenda import Agenda
from nutriciones.services.google.sheets.base import inserir_recurso
from nutriciones.services.google.sheets.types import PedidoInsercaoRecurso
from nutriciones.services.pacientes import generic_serializer

logger = logging.getLogger(__name__)

def criar_slot_agenda(
    data_slot: date,
    hora_inicio: time,
    hora_fim: time,
    slot_type: str = "consulta"
) -> str:
    """
    Cria um horário disponível na tabela de Agenda.
    Retorna o ID da agenda criada (agd_id).
    """
    agd_id = uuid.uuid4().hex
    agora = datetime.now()
    
    agenda = Agenda(
        agd_id=agd_id,
        data=data_slot,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        slot=slot_type,
        status="livre",
        ativo=True,
        created_at=agora.isoformat(),
        updated_at=agora.isoformat()
    )
    
    from nutriciones.core import config
    from nutriciones.services.google.sheets.base import sheet_name_of_resource_type
    
    logger.info(f"Criando Slot de Agenda para {data_slot} {hora_inicio.strftime('%H:%M')}")
    
    inserir_recurso(PedidoInsercaoRecurso(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Agenda],
        recurso=agenda,
        serialize=generic_serializer
    ))
    
    return agd_id
