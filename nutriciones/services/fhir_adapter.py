import json
from datetime import datetime
from typing import Any

from nutriciones.models.pacientes import Paciente, PacienteEmail, PacienteEndereco, PacienteTelefone
from nutriciones.models.consultas import Consulta
from nutriciones.models.planos import PlanoAlimentar
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.services.google.sheets import base
from nutriciones.services.google.sheets.types import PedidoListagemRecursos
from nutriciones.services.google.sheets.serializers.paciente import (
    deserialize_paciente, deserialize_email, deserialize_endereco, 
    deserialize_telefone, deserialize_consulta
)
from nutriciones.services.google.sheets.serializers.dieta import deserialize_plano
from nutriciones.core import config

def _get_resource[R](resource_type: type, resource_id: str, deserializer: Any) -> R | None:
    indices = get_indices()
    rng = indices.get_range_from_pk(resource_type, resource_id)
    if not rng:
        return None
    
    req = PedidoListagemRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=base.sheet_name_of_resource_type[resource_type],
        spreadsheet_range=rng.raw.split('!')[1],
        deserialize=deserializer
    )
    resources, _ = base.listar_recursos(req)
    return resources[0] if resources else None

def to_fhir_patient(pct_id: str) -> dict[str, Any]:
    """Converte Paciente para recurso FHIR Patient."""
    paciente = _get_resource(Paciente, pct_id, deserialize_paciente)
    if not paciente:
        return {}
        
    indices = get_indices()
    
    # Back-references para contatos
    email_ids = indices.get_back_references(Paciente, pct_id, PacienteEmail)
    tel_ids = indices.get_back_references(Paciente, pct_id, PacienteTelefone)
    adr_ids = indices.get_back_references(Paciente, pct_id, PacienteEndereco)
    
    telecom = []
    for mid in email_ids:
        m = _get_resource(PacienteEmail, mid, deserialize_email)
        if m: telecom.append({"system": "email", "value": m.email, "use": "home" if m.email_principal else "work"})
    for tid in tel_ids:
        t = _get_resource(PacienteTelefone, tid, deserialize_telefone)
        if t: telecom.append({"system": "phone", "value": f"+{t.ddi}{t.ddd}{t.telefone}", "use": "mobile" if t.whatsapp else "home"})
        
    address = []
    for aid in adr_ids:
        adr = _get_resource(PacienteEndereco, aid, deserialize_endereco)
        if adr:
            address.append({
                "line": [f"{adr.logradouro}, {adr.numero}", adr.complemento or ""],
                "city": adr.cidade, "state": adr.uf, "postalCode": adr.cep, "country": adr.pais
            })
            
    return {
        "resourceType": "Patient",
        "id": pct_id,
        "name": [{"family": paciente.sobrenome, "given": [paciente.nome]}],
        "telecom": telecom,
        "gender": "unknown", # Não temos no modelo básico
        "birthDate": paciente.data_nascimento.isoformat(),
        "address": address,
        "active": paciente.ativo
    }

def to_fhir_encounter(cns_id: str) -> dict[str, Any]:
    """Converte Consulta para recurso FHIR Encounter."""
    consulta = _get_resource(Consulta, cns_id, deserialize_consulta)
    if not consulta:
        return {}
        
    status_map = {
        "agendado": "planned", "confirmado": "arrived", 
        "realizado": "finished", "cancelado": "cancelled"
    }
    
    return {
        "resourceType": "Encounter",
        "id": cns_id,
        "status": status_map.get(consulta.status, "unknown"),
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
        "subject": {"reference": f"Patient/{consulta.pct_id}"},
        "period": {"start": consulta.created_at.isoformat()}
    }

def to_fhir_nutrition_order(plano_id: str) -> dict[str, Any]:
    """Converte PlanoAlimentar para recurso FHIR NutritionOrder."""
    plano = _get_resource(PlanoAlimentar, plano_id, deserialize_plano)
    if not plano:
        return {}
        
    # Itens detalhados via JSON
    try:
        itens = json.loads(plano.itens_detalhados)
    except:
        itens = []
        
    nutrients = []
    for it in itens:
        nutrients.append({
            "modifier": [{"text": it.get("nome")}],
            "amount": {"value": it.get("peso_g"), "unit": "g"}
        })
        
    return {
        "resourceType": "NutritionOrder",
        "id": plano_id,
        "status": "active",
        "intent": "order",
        "patient": {"reference": f"Patient/{plano.pct_id}"},
        "encounter": {"reference": f"Encounter/{plano.cns_id}"} if plano.cns_id else None,
        "dateTime": datetime.now().isoformat(),
        "enteralFormula": {
            "baseFormulaProductName": f"Plano {plano.data}",
            "caloricDensity": {"value": plano.total_kcal, "unit": "kcal"}
        }
    }
