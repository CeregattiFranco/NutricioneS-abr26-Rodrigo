import logging
from datetime import datetime
from typing import List, Dict, Any

from nutriciones.models.prontuario import Prontuario
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.services.google.sheets.base import listar_recursos, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoListagemRecursos
from nutriciones.services.google.sheets.serializers.paciente import deserialize_prontuario
from nutriciones.core import config, get_base_logger

logger = get_base_logger("NSS-BIOMETRICS")

from nutriciones.models.biometria import ExameLaboratorial
from nutriciones.services.google.sheets.serializers.paciente import deserialize_exame

def extrair_exames_recentes(pct_id: str) -> List[Dict[str, Any]]:
    """Busca exames laboratoriais estruturados via OCR/Webhook."""
    indices = get_indices()
    from nutriciones.models.pacientes import Paciente
    exm_ids = indices.get_back_references(Paciente, pct_id, ExameLaboratorial)
    
    exames = []
    for exm_id in exm_ids:
        rng = indices.get_range_from_pk(ExameLaboratorial, exm_id)
        if not rng: continue
        
        req = PedidoListagemRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name=sheet_name_of_resource_type[ExameLaboratorial],
            spreadsheet_range=rng.raw.split('!')[1],
            deserialize=deserialize_exame
        )
        res, _ = listar_recursos(req)
        if res:
            e = res[0]
            status = "Alerta" if (e.valor < e.referencia_min or e.valor > e.referencia_max) else "Normal"
            exames.append({
                "parametro": e.parametro, "valor": e.valor, "unidade": e.unidade,
                "ref": f"{e.referencia_min}-{e.referencia_max}", "status": status
            })
    return exames

def extrair_historico_clinico(pct_id: str) -> List[Dict[str, Any]]:
    """
    Recupera a evolução cronológica dos 4 inputs (Objetivo, Diagnóstico, Conduta, Orientação).
    """
    indices = get_indices()
    prt_ids = indices.get_back_references(None, pct_id, Prontuario) # Ajustado conforme lógica de back-refs
    
    # Se os indices não suportarem None como sheet, buscar via Paciente
    from nutriciones.models.pacientes import Paciente
    prt_ids = indices.get_back_references(Paciente, pct_id, Prontuario)
    
    historico = []
    for prt_id in prt_ids:
        rng = indices.get_range_from_pk(Prontuario, prt_id)
        if not rng: continue
        
        req = PedidoListagemRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name=sheet_name_of_resource_type[Prontuario],
            spreadsheet_range=rng.raw.split('!')[1],
            deserialize=deserialize_prontuario
        )
        res, _ = listar_recursos(req)
        if res:
            p = res[0]
            historico.append({
                "data": p.created_at.isoformat(),
                "objetivo": p.objetivo,
                "diagnostico": p.diagnostico,
                "conduta": p.conduta,
                "orientacao": p.orientacao
            })
    
    return sorted(historico, key=lambda x: x["data"])

def calcular_gap_objetivo(historico: List[Dict[str, Any]]) -> str:
    """
    Lógica simples de análise de tendência baseada nos textos dos prontuários.
    """
    if len(historico) < 2:
        return "Dados insuficientes para análise de evolução."
    
    ultimo = historico[-1]
    penultimo = historico[-2]
    
    # Exemplo de lógica de IA (Stub):
    if ultimo["objetivo"] == penultimo["objetivo"]:
        return f"ALERTA: Objetivo estagnado há {len(historico)} consultas. Reavaliar Conduta."
    
    return "Paciente em evolução constante de metas."
