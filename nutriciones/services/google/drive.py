import logging
from nutriciones.services.google.auth_service import get_drive_service
from nutriciones.core import config

logger = logging.getLogger(__name__)

def find_patient_folder(pct_id: str) -> str:
    """
    Busca a pasta raiz do paciente cujo nome termina com '_{pct_id}'.
    Retorna o ID da pasta no Drive, ou None se não encontrar.
    """
    service = get_drive_service()
    
    query = f"mimeType='application/vnd.google-apps.folder' and name contains '_{pct_id}' and trashed=false"
    
    logger.info(f"Buscando pasta do paciente no Drive usando PCT_ID: {pct_id}...")
    try:
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if not items:
            logger.warning(f"Pasta para PCT_ID {pct_id} não foi encontrada no Drive.")
            return None
            
        for item in items:
            if item['name'].endswith(f"_{pct_id}"):
                logger.info(f"Pasta Encontrada: {item['name']} (ID: {item['id']})")
                return item['id']
                
        logger.info(f"Pasta Encontrada por substring parcial: {items[0]['name']} (ID: {items[0]['id']})")
        return items[0]['id']
    except Exception as e:
        logger.error(f"Erro ao buscar pasta do paciente com id {pct_id}: {e}")
        return None

def criar_pasta_paciente(nome: str, sobrenome: str, pct_id: str) -> str:
    service = get_drive_service()
    nome_pasta = f"{nome}-{sobrenome}_{pct_id}".lower().replace(" ", "-")
    
    parent_id = config.GoogleServices.nutriciones_folder_id
    parents = [parent_id] if parent_id else []
    
    file_metadata = {
        'name': nome_pasta,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': parents
    }
    
    logger.info(f"Criando pasta raiz do paciente: {nome_pasta}...")
    folder = service.files().create(body=file_metadata, fields='id').execute()
    folder_id = folder.get('id')
    logger.info(f"Pasta criada com Sucesso (ID: {folder_id})")
    return folder_id

def copiar_arquivos_iniciais_paciente(folder_id: str, nome: str):
    service = get_drive_service()
    
    prontuario_id = config.GoogleServices.doc_template_id
    if prontuario_id:
        copy_metadata = {
            'name': f"Prontuário - {nome}",
            'parents': [folder_id]
        }
        logger.info("Copiando template de Prontuário...")
        service.files().copy(fileId=prontuario_id, body=copy_metadata).execute()
        
    exams_id = config.GoogleServices.exams_sheet_template_id
    if exams_id:
        copy_metadata = {
            'name': f"Solicitação de Exames - {nome}",
            'parents': [folder_id]
        }
        logger.info("Copiando template de Exames...")
        service.files().copy(fileId=exams_id, body=copy_metadata).execute()
