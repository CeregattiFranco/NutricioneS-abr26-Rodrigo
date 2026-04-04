import logging
from nutriciones.services.google.auth_service import get_creds
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

def enviar_email_template(destinatario: str, assunto: str, template: str, contexto: dict):
    """Envia um e-mail baseado em um template (simulação por enquanto)."""
    creds = get_creds()
    service = build('gmail', 'v1', credentials=creds)
    
    # Placeholder: Em um sistema real, carregaríamos o HTML do template e injetaríamos o contexto
    corpo = f"Olá {contexto.get('nome')},\n\nSua consulta foi concluída com sucesso.\nVocê pode acessar seus documentos aqui: {contexto.get('link_drive')}\n\nAtenciosamente,\nEquipe NutricioneS Sabla"
    
    logger.info(f"O e-mail para {destinatario} com assunto '{assunto}' seria enviado agora com o template '{template}'.")
    # Para o escopo deste projeto, mantemos apenas o log das notificações
    print(f"--- SIMULAÇÃO DE EMAIL ---")
    print(f"Para: {destinatario}")
    print(f"Assunto: {assunto}")
    print(f"Corpo: {corpo}")
    print(f"--------------------------")
