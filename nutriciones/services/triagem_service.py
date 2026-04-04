import logging
from typing import Dict, Any
from nutriciones.models.triagem import TriagemPaciente
from nutriciones.models.primary_key import PrimaryKey
from nutriciones.core import get_base_logger

logger = get_base_logger("NSS-TRIAGE")

def calcular_escores_triagem(pct_id: str, respostas: Dict[str, Any]) -> TriagemPaciente:
    """
    Processamento Stateless dos Scores do Perfil Dominante.
    Mapeia respostas de formulário (escala 0-3) em scores clínicos.
    """
    logger.info(f"[INFO] [NSS-TRIAGE] - Calculando scores para paciente {pct_id}")
    
    # Mapeamento simplificado (5 dimensões x 3 perguntas cada)
    # Em produção, as chaves viriam do Google Forms (ex: 'entry.12345')
    
    m = sum([respostas.get(f'm{i}', 0) for i in range(1, 4)]) # Metabólica
    e = sum([respostas.get(f'e{i}', 0) for i in range(1, 4)]) # Emocional
    c = sum([respostas.get(f'c{i}', 0) for i in range(1, 4)]) # Custo Energia
    u = sum([respostas.get(f'u{i}', 0) for i in range(1, 4)]) # Urgência
    s = sum([respostas.get(f's{i}', 0) for i in range(1, 4)]) # Segurança

    # Lógica do Perfil Dominante (O maior score ganha a cor)
    scores = {"Metabolica": m, "Emocional": e, "CustoEnergia": c, "Urgencia": u, "Seguranca": s}
    dominante = max(scores, key=scores.get)
    
    # Se o score for muito baixo (Verde), senão Amarelo/Vermelho
    if scores[dominante] > 7:
        perfil = f"VERMELHO_{dominante}"
    elif scores[dominante] > 4:
        perfil = f"AMARELO_{dominante}"
    else:
        perfil = "VERDE_ESTAVEL"

    return TriagemPaciente(
        tri_id=PrimaryKey.generate("TRI"),
        pct_id=pct_id,
        escore_metabolico=m,
        escore_emocional=e,
        escore_custo_energia=c,
        escore_urgencia=u,
        escore_seguranca=s,
        perfil_dominante=perfil
    )
