import logging
import io
from googleapiclient.http import MediaIoBaseUpload
from nutriciones.services.google.auth_service import get_drive_service

logger = logging.getLogger(__name__)

def upload_file_to_folder(file_content: bytes, filename: str, folder_id: str, mimetype: str = 'application/pdf') -> str:
    """Carrega um arquivo para uma pasta específica do Google Drive."""
    service = get_drive_service()
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mimetype, resumable=True)
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    file_id = uploaded_file.get('id')
    logger.info(f"Arquivo '{filename}' carregado com sucesso para a pasta {folder_id}. ID: {file_id}")
    return file_id
