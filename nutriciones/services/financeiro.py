import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

def criar_pagamento(cns_id: str, valor: float, metodo: str = "PIX") -> dict:
    """Simula a geração de um registro de pagamento/link PIX."""
    logger.info(f"Gerando pagamento de R$ {valor:.2f} para consulta {cns_id} via {metodo}...")
    
    pag_id = f"PAG-{uuid.uuid4().hex[:8].upper()}"
    return {
        "pagamento_id": pag_id,
        "consulta_id": cns_id,
        "valor": valor,
        "metodo": metodo,
        "status": "pendente",
        "timestamp": datetime.now().isoformat()
    }

def emitir_nota_fiscal_servico(cns_id: str) -> dict:
    """Simula a emissão de nota fiscal e retorna bytes fake para o PDF."""
    logger.info(f"Emitindo NF-e para consulta {cns_id}...")
    
    nfe_numero = f"NF-{uuid.uuid4().hex[:6].upper()}"
    fake_pdf_content = b"%PDF-1.4 Fake NF-e Content for " + cns_id.encode()
    
    return {
        "nfe_numero": nfe_numero,
        "pdf_content": fake_pdf_content,
        "status": "emitido"
    }
