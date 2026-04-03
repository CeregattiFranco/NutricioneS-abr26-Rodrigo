import io
import json
import logging
import datetime

from googleapiclient.http import MediaIoBaseUpload
from nutriciones.core import config
from nutriciones.services.google.auth_service import get_docs_service, get_drive_service
from nutriciones.services.google.drive import find_patient_folder

logger = logging.getLogger(__name__)

def gerar_pdf_plano_semanal(cns_id: str, resumo_semana: dict, planos_diarios: list[dict]) -> str:
    """
    Duplica o Doc Template, substitui chaves mestre, exporta em PDF 
    e envia pra dentro do folder do paciente baseado no CNS_ID.
    
    Placeholder suportados no docs template:
    {{data}}
    {{kcal}}
    {{proteina}}
    {{carboidrato}}
    {{lipidios}}
    {{itens}} - Agora vai renderizar o quadro completo dos 7 dias organizados.
    """
    template_id = config.GOOGLE_DOC_TEMPLATE_ID
    if not template_id:
        raise ValueError("Variável GOOGLE_DOC_TEMPLATE_ID ausente no config/env.")
        
    drive_service = get_drive_service()
    docs_service = get_docs_service()
    
    data_formatada = datetime.datetime.now().strftime("%d/%m/%Y")
    nome_doc = f"Plano Alimentar Semanal - {data_formatada}"
    
    # 1. Duplica Template Original
    logger.info(f"Gerando cópia do Template Original {template_id}...")
    copy_metadata = {'name': f"TEMP_{nome_doc}"} 
    copia = drive_service.files().copy(fileId=template_id, body=copy_metadata).execute()
    doc_id = copia.get('id')
    logger.info(f"Nova Instância do Documento Gerada: ID {doc_id}")
    
    # 2. Formata a tabela / listagem semanal de texto final pro paciente ler
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
    
    # 3. Dispara Replace de Textos Lotes no Doc usando o batchUpdate
    requests = [
        {'replaceAllText': {'containsText': {'text': '{{data}}', 'matchCase': True}, 'replaceText': str(data_formatada)}},
        {'replaceAllText': {'containsText': {'text': '{{kcal}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('kcal_media', 0)} kcal/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{proteina}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('proteina_media', 0)} g/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{carboidrato}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('carboidrato_media', 0)} g/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{lipidios}}', 'matchCase': True}, 'replaceText': f"{resumo_semana.get('lipidios_media', 0)} g/dia"}},
        {'replaceAllText': {'containsText': {'text': '{{itens}}', 'matchCase': True}, 'replaceText': itens_str}}
    ]
    
    logger.info("Refletindo Placeholders no Banco Text-to-Doc...")
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    # 4. Buscando Pasta do Paciente Através do cns_id
    folder_id = find_patient_folder(cns_id)
    parents = [folder_id] if folder_id else []
        
    # 5. Exportar do Google Docs para Bytestream em formato PDF
    logger.info("Exportando Documento Modificado para formatação PDF Raw Bytes...")
    request_pdf = drive_service.files().export_media(fileId=doc_id, mimeType='application/pdf')
    pdf_content = request_pdf.execute()
    
    # 6. Upload do Arquivo PDF dentro da Estrutura
    file_metadata = {
        'name': f"{nome_doc}.pdf",
        'parents': parents
    }
    media = MediaIoBaseUpload(io.BytesIO(pdf_content), mimetype='application/pdf', resumable=True)
    
    logger.info(f"Enviando PDF definitivo {'para a pasta ' + folder_id if folder_id else 'para a raiz do Drive'}...")
    uploaded_pdf = drive_service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id'
    ).execute()
    final_pdf_id = uploaded_pdf.get('id')
    logger.info(f"O PDF foi salvo na cloud Google com Sucesso! Identificador Final: {final_pdf_id}")
    
    # 7. Discard do Documento Temporário Raw do Docs para evitar poluição no Driver
    logger.info(f"Limpando o rastro Doc text (Apagando Doc ID: {doc_id})...")
    drive_service.files().delete(fileId=doc_id).execute()
    
    return final_pdf_id
