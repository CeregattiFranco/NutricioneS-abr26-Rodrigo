import logging
from typing import Dict, Any
from nutriciones.models.triagem import TriagemPerfil
from nutriciones.models.primary_key import PrimaryKey
import uuid
from nutriciones.core import get_base_logger

logger = get_base_logger("NSS-TRIAGE")

def processar_respostas_triage(pct_id: str, respostas: Dict[str, Any]) -> TriagemPerfil:
    """
    Motor de Triagem do Perfil Dominante.
    Mapeia respostas de formulário (escala 0-3) em scores clínicos e semáforos.
    Regras: 0-4 Verde, 5-8 Amarelo, 9+ Vermelho.
    """
    logger.info(f"[INFO] [NSS-TRIAGE] - Processando Triagem para paciente {pct_id}")
    
    # 5 dimensões x 3 perguntas cada
    m = sum([respostas.get(f'm{i}', 0) for i in range(1, 4)]) # Metabólica
    b = sum([respostas.get(f'b{i}', 0) for i in range(1, 4)]) # Comportamental
    e = sum([respostas.get(f'e{i}', 0) for i in range(1, 4)]) # Execução
    p = sum([respostas.get(f'p{i}', 0) for i in range(1, 4)]) # Expectativa
    s = sum([respostas.get(f's{i}', 0) for i in range(1, 4)]) # Segurança

    # Lógica do Perfil Dominante
    scores = {
        "METABOLICO": m, 
        "COMPORTAMENTAL": b, 
        "EXECUCAO": e, 
        "EXPECTATIVA": p, 
        "SEGURANCA": s
    }
    bloco_dominante = max(scores, key=scores.get)
    max_score = scores[bloco_dominante]
    
    # Semáforo de Risco
    if max_score >= 9:
        status = "VERMELHO"
    elif max_score >= 5:
        status = "AMARELO"
    else:
        status = "VERDE"

    dominante_final = f"{status}_{bloco_dominante}"

    return TriagemPerfil(
        tri_id=f"TRI_{uuid.uuid4().hex[:7]}",
        pct_id=pct_id,
        score_metabolico=m,
        score_comportamental=b,
        score_execucao=e,
        score_expectativa=p,
        score_seguranca=s,
        dominante_sugerido=dominante_final
    )
