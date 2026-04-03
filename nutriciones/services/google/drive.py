import logging
from nutriciones.services.google.auth_service import get_drive_service

logger = logging.getLogger(__name__)

def find_patient_folder(cns_id: str) -> str:
    """
    Busca a pasta raiz do paciente cujo nome termina com '_{cns_id}'.
    Retorna o ID da pasta no Drive, ou None se não encontrar.
    """
    service = get_drive_service()
    
    # Busca por mimeType de Folder e que o nome contenha o sufixo _ID (Regra estipulada)
    query = f"mimeType='application/vnd.google-apps.folder' and name contains '_{cns_id}' and trashed=false"
    
    logger.info(f"Buscando pasta do paciente no Drive usando CNS_ID: {cns_id}...")
    try:
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if not items:
            logger.warning(f"Pasta para CNS_ID {cns_id} não foi encontrada no Drive.")
            return None
            
        # Refinação: se tem multiplos matches, busca o que casa exatamente no final com _cns_id
        for item in items:
            if item['name'].endswith(f"_{cns_id}"):
                logger.info(f"Pasta Encontrada: {item['name']} (ID: {item['id']})")
                return item['id']
                
        # Fallback
        logger.info(f"Pasta Encontrada por substring parcial: {items[0]['name']} (ID: {items[0]['id']})")
        return items[0]['id']
    except Exception as e:
        logger.error(f"Erro ao buscar pasta do paciente com id {cns_id}: {e}")
        return None
