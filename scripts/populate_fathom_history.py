import os
import sys
import logging
from datetime import datetime

# Garante que o diretório raiz está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nutriciones.core import config, get_base_logger
from nutriciones.services.fathom_service import FathomClient, map_fathom_to_model
from nutriciones.models.fathom import FathomCall
from nutriciones.services.google.sheets.base import inserir_lista_recursos, PedidoInsercaoListaRecursos, listar_recursos
from nutriciones.services.google.sheets.serializers.fathom import serialize_fathom_call, deserialize_fathom_call
from nutriciones.services.google.sheets.indices import refresh_indices
from nutriciones.services.google.sheets.types import PedidoListagemRecursos

logger = get_base_logger("NSS-POPULATION")

def populate_complete_history():
    """Varre todo o histórico do Fathom e salva com detalhes completos no SSoT (40 colunas)."""
    try:
        client = FathomClient()
        logger.info("🚀 Iniciando varredura histórica DETALHADA (40 colunas)...")
        
        # 1. Carregar o que já existe na planilha para evitar duplicatas baseadas no recording_id
        logger.info("Verificando registros existentes na db_fathom...")
        registros_atuais = listar_recursos(PedidoListagemRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name="db_fathom",
            spreadsheet_range="A:AN",
            deserialize=deserialize_fathom_call
        ))
        
        ids_processados = set()
        if registros_atuais:
            # Pega a coluna recording_id (índice 4 no novo layout)
            for call in registros_atuais:
                if call and hasattr(call, 'recording_id') and call.recording_id:
                    ids_processados.add(str(call.recording_id))

        # 2. Lista as chamadas do Fathom
        reunioes_brutas = client.listar_todas_as_chamadas()
        if not reunioes_brutas:
            logger.warning("Nenhuma reunião encontrada.")
            return

        logger.info(f"Encontradas {len(reunioes_brutas)} reuniões. Processando novas...")
        
        recursos = []
        for info_basica in reunioes_brutas:
            meeting_id = str(info_basica.get("id"))
            
            if meeting_id in ids_processados:
                continue

            logger.info(f"Processando nova reunião: {meeting_id}")
            full_data = client.buscar_detalhes(meeting_id)
            if not full_data: 
                full_data = info_basica
            
            # Garante que temos o ID correto para o mapeamento
            if "id" not in full_data: 
                full_data["id"] = meeting_id
                
            call = map_fathom_to_model(full_data)
            recursos.append(call)
            
        # 3. Inserir
        if recursos:
            logger.info(f"Enviando {len(recursos)} registros para a planilha...")
            inserir_lista_recursos(PedidoInsercaoListaRecursos(
                spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
                spreadsheet_name="db_fathom",
                recursos=recursos,
                serialize=serialize_fathom_call
            ))
            refresh_indices(acknowledge_costly_operation=True)
            logger.info("✅ Carga concluída!")
        else:
            logger.info("Nenhum registro novo para inserir.")
        
    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)

if __name__ == "__main__":
    populate_complete_history()
