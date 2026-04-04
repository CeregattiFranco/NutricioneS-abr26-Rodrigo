import io
import json
import logging
import datetime

from googleapiclient.http import MediaIoBaseUpload
from nutriciones.core import config
from nutriciones.services.google.auth_service import get_docs_service, get_drive_service
from nutriciones.services.google.drive import find_patient_folder

from typing import TypeAlias

logger = logging.getLogger(__name__)

type GoogleDocIdStr = str

def criar_plano_alimentar_semanal(pct_id: str, resumo_semana: dict, planos_diarios: list[dict], nome_paciente: str = "Paciente", sobrenome_paciente: str = "") -> GoogleDocIdStr:
    """
    Duplica o Doc Template, substitui chaves mestre, exporta em PDF 
    e envia obrigatoriamente para a pasta do paciente.
    """
    template_id = config.GoogleServices.doc_template_id
    if not template_id:
        raise ValueError("Variável GOOGLE_DOC_TEMPLATE_ID ausente no config/env.")
        
    drive_service = get_drive_service()
    docs_service = get_docs_service()
    
    data_formatada = datetime.datetime.now().strftime("%d-%m-%Y")
    nome_doc_pdf = f"Plano_Alimentar_Semanal_{nome_paciente.replace(' ', '_')}_{data_formatada}.pdf"
    
    # 1. Duplica Template Original
    logger.info(f"Gerando instância temporária do Template para {nome_paciente}...")
    copy_metadata = {'name': f"TEMP_PLANO_{pct_id}"} 
    copia = drive_service.files().copy(fileId=template_id, body=copy_metadata).execute()
    doc_id = copia.get('id')
    
    # 2. Formata a tabela / listagem semanal
    itens_str = ""
    for plano in planos_diarios:
        dia = plano.get("dia", "DIA")
        totais_dia = plano.get("totais", {})
        itens_dia = plano.get("itens_detalhados", [])
        
        itens_str += f"\n--- {dia.upper()} ---\n"
        itens_str += f"Total: {totais_dia.get('kcal',0)} kcal | Prot: {totais_dia.get('proteina_g',0)}g | Carb: {totais_dia.get('carboidratos_g',0)}g | Lip: {totais_dia.get('lipidios_g',0)}g\n\n"
        
        for it in itens_dia:
            itens_str += f"  • {it['nome']} - {it['peso_g']}g ({it['kcal']} kcal)\n"
        itens_str += "\n"
    
    # 3. Dispara Replace de Textos
    requests = [
        {'replaceAllText': {'containsText': {'text': '{{data}}', 'matchCase': True}, 'replaceText': str(data_formatada)}},
        {'replaceAllText': {'containsText': {'text': '{{kcal}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('kcal_media', 0)} kcal/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{proteina}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('proteina_media', 0)} g/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{carboidrato}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('carboidrato_media', 0)} g/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{lipidios}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('lipidios_media', 0)} g/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{itens}}', 'matchCase': True}, 'replaceText': itens_str}}
    ]
    
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    # 4. Busca ou Cria a Pasta do Paciente (Contextualização Total)
    folder_id = find_patient_folder(pct_id, nome=nome_paciente, sobrenome=sobrenome_paciente)
    if not folder_id:
        logger.error(f"Impossível prosseguir sem pasta de destino para o PDF do paciente {pct_id}")
        return ""
        
    # 5. Exportar para PDF
    logger.info("Exportando Documento para PDF...")
    request_pdf = drive_service.files().export_media(fileId=doc_id, mimeType='application/pdf')
    pdf_content = request_pdf.execute()
    
    # 6. Upload do PDF na pasta do paciente
    file_metadata = {
        'name': nome_doc_pdf,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(io.BytesIO(pdf_content), mimetype='application/pdf', resumable=True)
    
    uploaded_pdf = drive_service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id'
    ).execute()
    
    final_pdf_id = uploaded_pdf.get('id')
    
    # 7. Limpeza
    drive_service.files().delete(fileId=doc_id).execute()
    
    return final_pdf_id
