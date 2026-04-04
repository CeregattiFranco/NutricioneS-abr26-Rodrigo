import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from nutriciones.models.agenda import Agenda
from nutriciones.models.consultas import Consulta
from nutriciones.models.pacientes import Paciente
from nutriciones.models.mensagens import Mensagem
from nutriciones.models.prontuario import Prontuario
from nutriciones.services.google.sheets.base import listar_recursos, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoListagemRecursos
from nutriciones.services.google.sheets.serializers.paciente import (
    deserialize_paciente, deserialize_consulta, deserialize_mensagem, 
    deserialize_prontuario
)
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.services.google.drive import find_patient_folder
from nutriciones.core import config
from nutriciones.services.google.gmail import enviar_email_template

logger = logging.getLogger(__name__)

def gerar_digest_diario() -> str:
    """
    Coleta dados de e-mails, agenda e prontuários para gerar um resumo executivo para o profissional.
    """
    logger.info("Gerando Digest Diário de Inteligência Clínica...")
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)
    amanha = hoje + timedelta(days=1)
    
    indices = get_indices()
    
    # 1. Buscar Mensagens (E-mails) das últimas 24h
    mensagens_recentes = _buscar_mensagens_periodo(ontem, hoje)
    
    # 2. Buscar Agenda de Hoje e Amanhã
    agenda_hoje = _buscar_consultas_data(hoje)
    agenda_amanha = _buscar_consultas_data(amanha)
    
    # 3. Cruzamento de Contexto
    digest_data = []
    for cns in agenda_hoje:
        pct_id = cns.pct_id
        paciente = _get_resource_local(Paciente, pct_id, deserialize_paciente)
        
        # Último prontuário
        prt_ids = indices.get_back_references(Paciente, pct_id, Prontuario)
        ultimo_prt = None
        if prt_ids:
            # Pegamos o último da lista (assumindo ordem cronológica nas inserções)
            ultimo_prt = _get_resource_local(Prontuario, prt_ids[-1], deserialize_prontuario)
            
        # Mensagens pendentes desse paciente
        msgs_pct = [m for m in mensagens_recentes if m.pct_id == pct_id]
        
        # Link do Drive
        folder_id = find_patient_folder(pct_id)
        link_drive = f"https://drive.google.com/drive/folders/{folder_id}" if folder_id else "#"
        
        digest_data.append({
            "paciente": f"{paciente.nome} {paciente.sobrenome}" if paciente else pct_id,
            "status": cns.status,
            "ultimo_objetivo": ultimo_prt.objetivo if ultimo_prt else "Nenhum registro anterior",
            "msgs_recentes": [m.resumo_ia for m in msgs_pct],
            "link_drive": link_drive
        })
        
    return _formatar_e_enviar_digest(digest_data, agenda_amanha)

def _get_resource_local(resource_type, pk, deserializer):
    indices = get_indices()
    rng = indices.get_range_from_pk(resource_type, pk)
    if not rng: return None
    
    req = PedidoListagemRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[resource_type],
        spreadsheet_range=rng.raw.split('!')[1],
        deserialize=deserializer
    )
    res, _ = listar_recursos(req)
    return res[0] if res else None

def _buscar_mensagens_periodo(inicio, fim):
    req = PedidoListagemRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Mensagem],
        spreadsheet_range="A2:K",
        deserialize=deserialize_mensagem
    )
    msgs, _ = listar_recursos(req)
    return [m for m in msgs if m.created_at >= inicio]

def _buscar_consultas_data(data_ref):
    req = PedidoListagemRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Consulta],
        spreadsheet_range="A2:L",
        deserialize=deserialize_consulta
    )
    consultas, _ = listar_recursos(req)
    # No stub, filtramos por data de criação / agenda se houver
    # Simplificação: retornamos as que estão no SSoT
    return [c for c in consultas if c.status in ['agendado', 'confirmado']]

from nutriciones.services.search.firecrawler import buscar_atualizacao_cientifica

def _formatar_e_enviar_digest(hoje_data, amanha_lista):
    corpo = "--- DIGEST DIÁRIO NUTRICIONES ---\n\n"
    
    # 0. Curadoria Científica do Dia (NSS Intelligence)
    if hoje_data:
        tema_dia = hoje_data[0]["ultimo_objetivo"][:30] # Pega o tema do primeiro paciente
        curadoria = buscar_atualizacao_cientifica(tema_dia)
        corpo += f"🔬 CURADORIA CIENTÍFICA DO DIA: {tema_dia}\n"
        corpo += f"{curadoria}\n"
        corpo += "---------------------------------\n\n"
    
    corpo += f"AGENDA DE HOJE ({len(hoje_data)} consultas):\n"
    for item in hoje_data:
        corpo += f"- {item['paciente']} [{item['status'].upper()}]\n"
        corpo += f"  Última Meta: {item['ultimo_objetivo']}\n"
        if item['msgs_recentes']:
            corpo += f"  Novas Mensagens: {', '.join(item['msgs_recentes'])}\n"
        corpo += f"  Pasta Drive: {item['link_drive']}\n\n"
        
    corpo += f"\nRESUMO AMANHÃ: {len(amanha_lista)} consultas agendadas."
    
    logger.info("Enviando Digest por e-mail para o Profissional...")
    enviar_email_template(
        destinatario=config.GoogleServices.admin_email or "coach@nutriciones.com",
        assunto=f"Seu Digest Diário - {datetime.now().strftime('%d/%m')}",
        template="digest_diario",
        contexto={"corpo_digest": corpo}
    )
    return corpo
