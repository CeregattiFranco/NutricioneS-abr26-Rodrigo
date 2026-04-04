import requests
from nutriciones.core import config, get_base_logger

logger = get_base_logger("NSS-FATHOM")

class FathomClient:
    """Cliente para integração com a API do Fathom AI."""
    def __init__(self, api_key: str = config.FATHOM_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.fathom.video/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def buscar_detalhes_chamada(self, call_id: str) -> dict:
        """Recupera os detalhes e o resumo estruturado (SOPP) da chamada."""
        if not self.api_key:
            return {"error": "API Key do Fathom não configurada."}
        logger.info(f"[INFO] [NSS-FATHOM] - Buscando detalhes da chamada Fathom: {call_id}")
        return {
            "call_id": call_id,
            "transcript_summary": "Mock summary for development."
        }

import uuid
import json
from nutriciones.models.fathom import FathomCall
from nutriciones.models.rascunhos import RascunhoClinico
from nutriciones.services.google.sheets.base import inserir_lista_recursos, sheet_name_of_resource_type, listar_recursos, PedidoInsercaoListaRecursos
from nutriciones.services.google.sheets.types import PedidoListagemRecursos
from nutriciones.services.google.sheets.indices import get_indices, refresh_indices
from nutriciones.services.pacientes import generic_serializer

def sync_fathom_data():
    """Busca novas chamadas Fathom e persiste no SSoT (Stateless)."""
    logger.info("[INFO] [NSS-FATHOM] - Iniciando sincronização de chamadas Fathom.")
    
    indices = get_indices()
    r = indices.redis_client
    
    try:
        client = FathomClient()
        # Em produção, buscaríamos uma lista das últimas chamadas
        # Para este módulo, simulamos o recebimento e cruzamento
        call_id = "CALL_" + uuid.uuid4().hex[:6]
        
        # 1. Checar se já processamos (Fator VI - Redis)
        if r and r.exists(f"nss:fathom:processed:{call_id}"):
            logger.info(f"[INFO] [NSS-FATHOM] - Chamada {call_id} já processada anteriormente.")
            return

        detalhes = client.buscar_detalhes_chamada(call_id)
        
        # 2. Tentar cruzamento com Consulta (Deveria buscar via timestamp)
        cns_id = "CNS_CORRELATED_01" # Mock do cruzamento
        
        nova_call = FathomCall(
            fth_id=uuid.uuid4().hex[:10],
            cns_id=cns_id,
            fathom_call_id=call_id,
            summary_status="ready",
            transcript_url=f"https://fathom.video/share/{call_id}"
        )
        
        inserir_lista_recursos(PedidoInsercaoListaRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name=sheet_name_of_resource_type[FathomCall],
            recursos=[nova_call],
            serialize=generic_serializer
        ))
        
        # Marcar no Redis
        if r:
            r.set(f"nss:fathom:processed:{call_id}", "done", ex=86400*7) # Cache por 7 dias
            
        logger.info(f"[INFO] [NSS-FATHOM] - Chamada {call_id} persistida e cruzada com {cns_id}.")
        refresh_indices(acknowledge_costly_operation=True)
        
    except Exception as e:
        logger.error(f"[ERROR] [NSS-FATHOM] - Falha na sincronização Fathom: {e}")

def process_fathom_summary(fth_id: str):
    """Transforma o resumo bruto em rascunhos de prontuário (4 inputs)."""
    logger.info(f"[INFO] [NSS-FATHOM] - Processando resumo clínico para Fathom ID {fth_id}.")
    # Aqui entraria a lógica de chamada ao Agente Ph.D. configurada no nutricionista_agent.py
    # O agente extrairia os 4 inputs e persistiria na db_rascunhos_clinicos.
