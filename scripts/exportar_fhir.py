import json
import sys
import os
from pathlib import Path

# Setup Pathlib/Rebirth
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.fhir_adapter import to_fhir_patient, to_fhir_encounter, to_fhir_nutrition_order
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.models.pacientes import Paciente
from nutriciones.models.consultas import Consulta
from nutriciones.models.planos import PlanoAlimentar

def exportar_fhir_completo(pct_id: str):
    """Gera um Bundle FHIR completo para um paciente."""
    print(f"[*] Gerando Bundle FHIR para o paciente: {pct_id}...")
    
    patient_res = to_fhir_patient(pct_id)
    if not patient_res:
        print(f"[X] Paciente {pct_id} não encontrado no SSoT.")
        return

    indices = get_indices()
    
    # Bundle entries
    entries = [{"resource": patient_res}]
    
    # Consultas (Encounters)
    cns_ids = indices.get_back_references(Paciente, pct_id, Consulta)
    for cid in cns_ids:
        entries.append({"resource": to_fhir_encounter(cid)})
        
    # Planos (NutritionOrder)
    plano_ids = indices.get_back_references(Paciente, pct_id, PlanoAlimentar)
    for pid in plano_ids:
        entries.append({"resource": to_fhir_nutrition_order(pid)})
        
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries
    }
    
    output_path = Path("data") / f"fhir_bundle_{pct_id}.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)
        
    print(f"[✔] Bundle FHIR exportado com sucesso para {output_path}")

if __name__ == "__main__":
    # Exemplo com ID de teste (se houver nos índices)
    import sys
    test_id = sys.argv[1] if len(sys.argv) > 1 else "paciente-teste-123"
    try:
        exportar_fhir_completo(test_id)
    except Exception as e:
        print(f"[X] Erro ao exportar FHIR: {e}")
