import logging
import uuid
from datetime import datetime

from nutriciones.models.prontuario import Prontuario
from nutriciones.models.pacientes import Paciente
from nutriciones.models.consultas import Consulta
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.services.google.sheets.base import inserir_recurso, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoInsercaoRecurso
from nutriciones.services.pacientes import generic_serializer
from nutriciones.services.google.drive import find_patient_folder, find_clinical_record
from nutriciones.services.google.auth_service import get_docs_service
from nutriciones.services.google.gmail import enviar_email_template
from nutriciones.core import config

logger = logging.getLogger(__name__)

def processar_inputs_clinicos(cns_id: str, objetivo: str, diagnostico: str, conduta: str, orientacao: str):
    """
    Orquestra o registro técnico e o disparo de orientações pós-consulta.
    """
    indices = get_indices()
    
    # 1. Recuperar Contexto O(1)
    pct_id = indices.get_fk(Consulta, cns_id, Paciente)
    if not pct_id:
        logger.error(f"Paciente não encontrado para a consulta {cns_id}")
        return

    # 2. Persistência Atômica no SSoT (db_prontuarios)
    agora = datetime.now()
    prontuario = Prontuario(
        prt_id=uuid.uuid4().hex,
        cns_id=cns_id,
        pct_id=pct_id,
        objetivo=objetivo,
        diagnostico=diagnostico,
        conduta=conduta,
        orientacao=orientacao,
        created_at=agora,
        updated_at=agora
    )
    
    logger.info(f"Registrando prontuário clínico para consulta {cns_id}...")
    inserir_recurso(PedidoInsercaoRecurso(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[Prontuario],
        recurso=prontuario,
        serialize=generic_serializer
    ))

    # 3. Atualizar Documento Google Docs (Prontuário Digital)
    _escrever_no_documento_paciente(pct_id, objetivo, diagnostico, conduta, orientacao)

    # 4. Disparo Gmail: Orientações
    # Precisamos do e-mail do paciente (Placeholder ou via Indices)
    # Por agora, usamos a simulação do serviço de gmail
    enviar_email_template(
        destinatario="paciente@exemplo.com", 
        assunto="Orientações Pós-Consulta - NutricioneS",
        template="orientacoes_pos_consulta",
        contexto={
            "nome": "Paciente",
            "orientacao": orientacao
        }
    )

    # 5. Agendamento de CSAT (Stub)
    _agendar_fila_csat(cns_id, pct_id)

    logger.info(f"✅ Processamento clínico da consulta {cns_id} concluído com sucesso!")

def _escrever_no_documento_paciente(pct_id: str, obj: str, diag: str, cond: str, ori: str):
    """Insere os dados técnicos no arquivo de prontuário do Google Docs."""
    try:
        folder_id = find_patient_folder(pct_id)
        doc_id = find_clinical_record(folder_id, "")
        
        if not doc_id:
            logger.warning(f"Arquivo de prontuário não encontrado para o paciente {pct_id}")
            return
            
        docs_service = get_docs_service()
        data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        texto_inserir = (
            f"\n\n--- REGISTRO CLÍNICO EM {data_str} ---\n"
            f"OBJETIVO: {obj}\n"
            f"DIAGNÓSTICO: {diag}\n"
            f"CONDUTA: {cond}\n"
            f"ORIENTAÇÃO: {ori}\n"
        )
        
        requests = [{
            'insertText': {
                'location': {'index': 1}, # Insere no topo após o título
                'text': texto_inserir
            }
        }]
        
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        logger.info(f"Documento de prontuário {doc_id} atualizado com os novos inputs.")
    except Exception as e:
        logger.error(f"Erro ao escrever no Google Docs: {e}")

def _agendar_fila_csat(cns_id: str, pct_id: str):
    """Representação da fila de mensagens automáticas (Check-in T+2, CSAT T+3)."""
    logger.info(f"[STUB] Agendando e-mails de acompanhamento para 48h e 72h na db_mensagens para o paciente {pct_id}.")
