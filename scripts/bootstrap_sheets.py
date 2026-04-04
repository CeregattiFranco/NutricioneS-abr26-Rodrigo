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
    "db_triagem": ["tri_id", "pct_id", "score_metabolico", "score_comportamental", "score_execucao", "score_expectativa", "score_seguranca", "dominante_sugerido", "created_at"],
    "db_fathom": [
        "title", "meeting_title", "url", "share_url", "recording_id", "created_at",
        "scheduled_start_time", "scheduled_end_time", "recording_start_time", "recording_end_time",
        "calendar_invitees_domains_type", "transcript_language", "transcript", "default_summary",
        "action_items", "crm_matches", "recorded_by_name", "recorded_by_email", "recorded_by_email_domain",
        "recorded_by_team", "invitee_1_name", "invitee_1_email", "invitee_1_email_domain", "invitee_1_is_external",
        "invitee_1_matched_speaker_display_name", "invitee_2_name", "invitee_2_email", "invitee_2_email_domain",
        "invitee_2_is_external", "invitee_2_matched_speaker_display_name", "invitees_extra", "invitee_3_name",
        "invitee_3_email", "invitee_3_email_domain", "invitee_3_is_external", "invitee_3_matched_speaker_display_name",
        "summary_template_name", "summary_markdown", "summary_fetch_status", "summary_markdown_pt_br"
    ],
    "db_exames_laboratoriais": ["exm_id", "pct_id", "parametro", "valor", "unidade", "referencia_min", "referencia_max", "observacao", "data_exame", "created_at", "updated_at"],
    "db_rascunhos_clinicos": ["ras_id", "cns_id", "pct_id", "objetivo_sugerido", "diagnostico_sugerido", "conduta_sugerida", "orientacao_sugerida", "fonte", "status", "created_at"],
    "db_outcomes": ["out_id", "pct_id", "cns_id", "aderencia_autorreferida", "objetivo_atingido", "perfil_dominante_na_data", "data_registro"],
    "db_prontuarios": ["prt_id", "cns_id", "pct_id", "objetivo", "diagnostico", "conduta", "orientacao", "created_at", "updated_at"],
    "db_mensagens": ["msg_id", "pct_id", "origem", "assunto", "conteudo", "resumo_ia", "status", "template_name", "scheduled_at", "created_at", "updated_at"]
}

def bootstrap():
    # 1. Obter serviço e validar acesso
    try:
        service = get_ssot_sheets_service()
        if not service:
            logger.error("ERRO: Não foi possível obter o serviço do Google Sheets. Verifique o Onboarding.")
            return
    except Exception as e:
        logger.error(f"ERRO CRÍTICO na autenticação: {e}")
        return
        
    spreadsheet_id = config.GoogleServices.sheet_id_cardapio
    
    if not spreadsheet_id:
        logger.error("Erro: A variável de ambiente GOOGLE_SHEET_ID_CARDAPIO não foi carregada corretamente.")
        return

    # 2. Obter abas existentes
    logger.info(f"Conectando ao Google Sheets para a planilha principal de banco de dados...")
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    except Exception as e:
        logger.error(f"Erro ao ler os metadados da planilha: {e}")
        return
        
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
        
        # Limpa toda a aba para remover dados legados com esquema antigo
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"{table_name}!A:ZZ"
        ).execute()

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
