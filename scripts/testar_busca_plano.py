import sys
import os
from pathlib import Path

# Adiciona a raiz do projeto ao PYTHONPATH para permitir imports no script
sys.path.insert(0, str(Path(__file__).parent.parent))

from nutriciones.models.pacientes import Paciente
from nutriciones.models.planos import PlanoAlimentar
from nutriciones.services.google.sheets.indices import get_indices


def testar_busca_plano(paciente_id: str):
    print(f"Buscando Planos Alimentares para o paciente: {paciente_id}")

    try:
        # Recuperamos o cache binário (O(1) lookups)
        indices = get_indices()
    except FileNotFoundError:
        print("Arquivo de cache 'indices.bin' não encontrado. O sistema precisa ter preenchido o cache pelo menos uma vez.")
        return
    except Exception as e:
        print(f"Erro ao ler índices: {e}")
        return

    # A chamada O(1) do cache binário em memória para recuperar todas as FK's de Planos que mapeiam para este Paciente
    planos_ids = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key=paciente_id,
        primary_sheet=PlanoAlimentar
    )

    if not planos_ids:
        print(f"Nenhum Plano Alimentar vinculado ao paciente {paciente_id} foi encontrado nos índices.")
        return

    print("\n[✔] Planos Alimentares Encontrados:")
    for pk in planos_ids:
        print(f" - {pk}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        id_teste = sys.argv[1]
    else:
        # Um ID de fallback para teste padrão caso não seja passado argumento
        id_teste = "paciente-teste-123"
        
    testar_busca_plano(id_teste)
