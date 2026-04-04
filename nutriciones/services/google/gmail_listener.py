import base64
import logging
import uuid
import re
from datetime import datetime
from googleapiclient.discovery import build

from nutriciones.services.google.auth_service import get_creds
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.models.pacientes import PacienteEmail, Paciente
from nutriciones.models.mensagens import Mensagem
from nutriciones.services.google.sheets.base import inserir_recurso, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoInsercaoRecurso
from nutriciones.services.pacientes import generic_serializer
from nutriciones.services.google.drive import find_patient_folder
from nutriciones.services.google.drive_utils import upload_file_to_folder
from nutriciones.core import config

logger = logging.getLogger(__name__)

def listen_gmail_inbox():
    """
    Monitora a caixa de entrada para mensagens não lidas de pacientes 
    e orquestra o processamento de conteúdo e anexos.
    """
    creds = get_creds()
    service = build('gmail', 'v1', credentials=creds)
    
    # 1. Busca mensagens não lidas
    logger.info("Verificando mensagens não lidas no Gmail...")
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = results.get('messages', [])
    
    if not messages:
        logger.info("Nenhuma nova mensagem para processar.")
        return

    indices = get_indices()
    
    for msg_info in messages:
        try:
            msg = service.users().messages().get(userId='me', id=msg_info['id']).execute()
            
            # 2. Extração de Metadados
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sem Assunto")
            sender_raw = next((h['value'] for h in headers if h['name'] == 'From'), "")
            
            # Regex simples para extrair o e-mail
            email_match = re.search(r'<(.+?)>', sender_raw) or re.search(r'[\w\.-]+@[\w\.-]+', sender_raw)
            sender_email = email_match.group(1) if email_match else sender_raw.strip()
            
            # 3. Validação O(1) de Paciente
            pct_id = indices.user_emails.get(sender_email)
            if not pct_id:
                logger.info(f"Ignorando e-mail de {sender_email}: Não identificado como paciente.")
                continue
                
            logger.info(f"Processando e-mail de paciente identificado: {sender_email} (ID: {pct_id})")
            
            # 4. Extração do Corpo
            body = _get_message_body(msg)
            
            # 5. Inteligência IA: Resumo de Contexto (Auto 2)
            resumo = _gerar_resumo_contexto(subject, body)
            
            # Guardar na SSoT
            agora = datetime.now()
            mensagem_obj = Mensagem(
                msg_id=uuid.uuid4().hex,
                pct_id=pct_id,
                origem='email',
                assunto=subject,
                conteudo=body[:500], # Limitamos conteúdo bruto no log
                resumo_ia=resumo,
                status='pendente',
                created_at=agora,
                updated_at=agora
            )
            
            inserir_recurso(PedidoInsercaoRecurso(
                spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
                spreadsheet_name=sheet_name_of_resource_type[Mensagem],
                recurso=mensagem_obj,
                serialize=generic_serializer
            ))
            
            # 6. Organizador de Drive (Auto 7)
            if "EXAMES" in subject.upper():
                _process_attachments(service, msg, pct_id)
            
            # 7. Marcar como lido
            service.users().messages().modify(
                userId='me', 
                id=msg_info['id'], 
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Fluxo concluído para e-mail {msg_info['id']}.")

        except Exception as e:
            logger.error(f"Erro ao processar mensagem {msg_info['id']}: {e}")

def _get_message_body(msg):
    body = ""
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode()
                break
    elif 'body' in msg['payload']:
        body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode()
    return body

def _gerar_resumo_contexto(assunto, corpo):
    """Stub de IA para gerar resumo situacional (Integrar com GPT/Crew no futuro)."""
    # Simulação de IA simplificada
    if len(corpo) > 10:
        return f"Paciente enviou e-mail sobre '{assunto}'. Resumo: O conteúdo parece tratar de {corpo[:50]}..."
    return f"E-mail curto sobre {assunto}."

def _process_attachments(service, msg, pct_id):
    """Varre e faz upload de anexos de exames para o Drive do paciente."""
    if 'parts' not in msg['payload']:
        return

    folder_id = find_patient_folder(pct_id)
    if not folder_id:
        logger.warning(f"Pasta do paciente {pct_id} não encontrada para salvar exames.")
        return

    for part in msg['payload']['parts']:
        if part.get('filename'):
            attachment_id = part['body'].get('attachmentId')
            if attachment_id:
                attachment = service.users().messages().attachments().get(
                    userId='me', messageId=msg['id'], id=attachment_id
                ).execute()
                
                data = base64.urlsafe_b64decode(attachment['data'])
                filename = f"EXAME_{datetime.now().strftime('%Y%m%d')}_{part['filename']}"
                
                upload_file_to_folder(data, filename, folder_id, part['mimeType'])
                logger.info(f"Anexo '{filename}' salvo no Drive do paciente.")
