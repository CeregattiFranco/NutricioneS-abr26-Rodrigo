import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from nutriciones.models.mensagens import Mensagem
from nutriciones.models.pacientes import Paciente
from nutriciones.services.google.sheets.base import inserir_lista_recursos, listar_recursos, atualizar_recurso, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoInsercaoListaRecursos, PedidoListagemRecursos, PedidoAtualizacaoRecurso
from nutriciones.services.pacientes import generic_serializer
from nutriciones.services.google.sheets.serializers.paciente import deserialize_mensagem
from nutriciones.services.google.gmail import enviar_email_template
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.core import config

logger = logging.getLogger(__name__)

def agendar_sequencia_educativa(pct_id: str, tema: str):
    """
    Cria uma régua de conteúdo (D+3, D+7, D+12) na db_mensagens.
    """
    logger.info(f"Agendando sequência educativa sobre '{tema}' para o paciente {pct_id}...")
    
    agora = datetime.now()
    sequencia = [
        {"dias": 3, "assunto": f"Entendendo {tema} (Parte 1)"},
        {"dias": 7, "assunto": f"Dicas Práticas: {tema}"},
        {"dias": 12, "assunto": f"Desafio Final: {tema}"}
    ]
    
    novas_mensagens = []
    for etapa in sequencia:
        msg = Mensagem(
            msg_id=uuid.uuid4().hex,
            pct_id=pct_id,
            origem='campanha',
            assunto=etapa["assunto"],
            conteudo=f"Conteúdo automático sobre {tema}.",
            resumo_ia="Campanha Educativa",
            status='agendado',
            template_name=f"educativo_{tema.lower()}",
            scheduled_at=agora + timedelta(days=etapa["dias"]),
            created_at=agora,
            updated_at=agora
        )
        novas_mensagens.append(msg)
        
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Mensagem],
        recursos=novas_mensagens,
        serialize=generic_serializer
    ))
    logger.info(f"Régua de {len(novas_mensagens)} mensagens agendada.")

def processar_fila_mensagens():
    """
    Varre db_mensagens em busca de envios pendentes para hoje. (Motor Auto 4)
    """
    logger.info("Iniciando processamento de fila de mensagens agendadas...")
    
    # 1. Carregar mensagens (em um sistema real usaríamos filtros de data no Sheets API ou indices filtrados)
    # Aqui listamos todas em 'agendado' e filtramos localmente para simplificar
    req = PedidoListagemRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Mensagem],
        spreadsheet_range="A2:K", # Range incluindo novos campos
        deserialize=deserialize_mensagem
    )
    
    mensagens, range_info = listar_recursos(req)
    hoje = datetime.now()
    indices = get_indices()
    
    for msg in mensagens:
        if msg.status == 'agendado' and msg.scheduled_at and msg.scheduled_at <= hoje:
            logger.info(f"Disparando mensagem agendada: {msg.assunto} ({msg.msg_id})")
            
            # Buscar email do paciente via Indices
            # Para este stub, enviamos via template
            enviar_email_template(
                destinatario="paciente@exemplo.com", 
                assunto=msg.assunto,
                template=msg.template_name or "generico",
                contexto={"nome": "Paciente", "conteudo": msg.conteudo}
            )
            
            # Atualizar status para 'enviado' no SSoT
            # Precisamos do range para atualizar recurso. Podemos pegar via indices se pk existir
            msg_range = indices.get_range_from_pk(Mensagem, msg.msg_id)
            if msg_range:
                # Criamos uma cópia atualizada
                msg_atualizada = Mensagem(
                    **{**msg.__dict__, 'status': 'enviado', 'updated_at': datetime.now()}
                )
                atualizar_recurso(PedidoAtualizacaoRecurso(
                    spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
                    spreadsheet_name=sheet_name_of_resource_type[Mensagem],
                    spreadsheet_range=msg_range.raw.split('!')[1],
                    recurso=msg_atualizada,
                    serialize=generic_serializer
                ))
