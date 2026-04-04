import logging
from datetime import datetime, timedelta
from typing import List

from nutriciones.models.consultas import Consulta
from nutriciones.services.google.sheets.base import listar_recursos, atualizar_recurso, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoListagemRecursos, PedidoAtualizacaoRecurso
from nutriciones.services.google.sheets.serializers.paciente import deserialize_consulta
from nutriciones.services.pacientes import generic_serializer
from nutriciones.services.google.gmail import enviar_email_template
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.core import config

logger = logging.getLogger(__name__)

def rodar_regua_confirmacao():
    """
    Vae a db_consultas e dispara agendamentos com base na proximidade. (Auto 5)
    """
    logger.info("Iniciando Régua de Confirmação e Lembretes (NSS)...")
    
    indices = get_indices()
    
    # 1. Obter consultas (em um sistema real buscaríamos filtrado no Sheets)
    req = PedidoListagemRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Consulta],
        spreadsheet_range="A2:L",
        deserialize=deserialize_consulta
    )
    
    # Supomos que o serializer Consulta agora possui os 12 campos
    consultas, _ = listar_recursos(req)
    hoje = datetime.now()
    
    for cns in consultas:
        if cns.status not in ["agendado", "confirmado"]:
            continue
            
        # Simulação de data de consulta (no modelo Consulta atual, usamos created_at do objeto 
        # mas devemos ler a data do agendamento real via agenda_id se necessário)
        # Para este stub, usamos a data da agenda vinculada
        agenda_id = cns.agd_id
        # agd_range = indices.get_range_from_pk(Agenda, agenda_id)
        # Para simplificar o stub, assumimos uma data genérica para testes de régua
        # Em produção, buscaríamos Agenda.data
        data_consulta = hoje + timedelta(days=7) # Mock
        
        delta = data_consulta - hoje
        
        if timedelta(days=6, hours=23) < delta <= timedelta(days=7):
            _enviar_confirmacao(cns, "7 dias - Confirmação NutricioneS")
            
        elif timedelta(days=1, hours=23) < delta <= timedelta(days=2):
            _enviar_confirmacao(cns, "2 dias - Lembrete de Exames")

        elif timedelta(minutes=110) < delta <= timedelta(hours=2):
             _enviar_confirmacao(cns, "2 horas - Instruções de Acesso")

def _enviar_confirmacao(cns: Consulta, template: str):
    logger.info(f"Disparando e-mail template '{template}' para consulta {cns.cns_id}")
    enviar_email_template(
        destinatario="paciente@exemplo.com", 
        assunto=template,
        template=template,
        contexto={"id": cns.cns_id}
    )
