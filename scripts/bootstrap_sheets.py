import sys
import logging
from pathlib import Path

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from nutriciones.core import config
from nutriciones.services.google.auth_service import get_ssot_sheets_service

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mapeamento de cabeçalhos alinhado ESTRITAMENTE com a ordem dos campos nos Dataclasses
TABLE_SCHEMAS = {
    "db_pacientes": ["pct_id", "nome", "sobrenome", "cpf", "data_nascimento", "responsavel_id", "status", "origem", "ativo", "created_at", "updated_at"],
    "db_pacientes_telefones": ["tel_id", "pct_id", "ddi", "ddd", "telefone", "whatsapp", "contato_principal", "ativo", "created_at", "updated_at"],
    "db_pacientes_emails": ["mail_id", "pct_id", "email", "validado", "opt_in_data", "email_principal", "ativo", "created_at", "updated_at"],
    "db_pacientes_enderecos": ["adr_id", "pct_id", "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "pais", "endereco_nfse", "ativo", "created_at", "updated_at"],
    "db_agenda": ["agd_id", "data", "hora_inicio", "hora_fim", "slot", "status", "ativo", "created_at", "updated_at"],
    "db_consultas": ["cns_id", "pct_id", "agd_id", "consulta_perfil", "status", "ativo", "slot", "calendar_event_id", "meet_url", "calendar_event_url", "created_at", "updated_at"],
    "db_planosAlimentares": ["plano_id", "pct_id", "cns_id", "data", "total_kcal", "total_proteina", "total_carboidrato", "total_lipidios", "itens_detalhados"],
    "db_triagem": ["tri_id", "pct_id", "score_metabolico", "score_comportamental", "score_execucao", "score_expectativa", "score_seguranca", "dominante_sugerido", "created_at"]
}

def bootstrap():
    service = get_ssot_sheets_service()
    spreadsheet_id = config.GoogleServices.sheet_id_cardapio
    
    if not spreadsheet_id:
        logger.error("Erro: A variável de ambiente GOOGLE_SHEET_ID_CARDAPIO não foi carregada corretamente.")
        return

    # 1. Obter abas existentes
    logger.info(f"Conectando ao Google Sheets para a planilha principal de banco de dados...")
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    existing_sheet_names = [s.get("properties", {}).get("title") for s in sheets]

    for table_name, headers in TABLE_SCHEMAS.items():
        # 2. Criar aba se não existir
        if table_name not in existing_sheet_names:
            logger.info(f"Criando aba não existente: {table_name}")
            batch_update_request = {
                'requests': [{'addSheet': {'properties': {'title': table_name}}}]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_request).execute()
        
        # 3. Atualizar/Resetar cabeçalhos (Linha 1)
        logger.info(f"Configurando cabeçalhos de Model para aba: {table_name}")
        body = {'values': [headers]}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{table_name}!A1",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

    logger.info("✅ Bootstrap concluído! Planilha SSoT e índices prontos para receber dados nativos do NSS.")

if __name__ == "__main__":
    bootstrap()
