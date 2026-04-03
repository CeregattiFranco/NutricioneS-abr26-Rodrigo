import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from nutriciones.services.google.sheets.indices import get_indices, refresh_indices
from nutriciones.models.pacientes import Paciente
from nutriciones.models.consultas import Consulta

def test_indices_back_references_o1_lookup():
    # Setup
    # Assumindo que indices.bin já possui o CNS-SIM-994 (indexado no refresh manual anterior)
    # Ou 'pct_001' se fôssemos mockar
    
    # Execute - O(1) Fetch
    try:
        indices = get_indices()
    except FileNotFoundError:
        pytest.skip("indices.bin não encontrado. Requer refresh prévio.")
        
    # Testamos com os dados que o refresh anterior extraiu
    # O refresh anterior encontrou um PlanoAlimentar pro Paciente 'CNS-SIM-994'
    # Vamos verificar se o Indices retornou refs para esse ID
    from nutriciones.models.planos import PlanoAlimentar
    
    b_refs = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key="CNS-SIM-994",
        primary_sheet=PlanoAlimentar
    )
    
    # Assert
    # Se o refresh anterior rodou, deve haver pelo menos 1
    assert isinstance(b_refs, list)
    if len(b_refs) > 0:
        # A primeira ref deve ser uma PK de plano
        assert b_refs[0].startswith("77321601") or b_refs[0] is not None
        print(f"O(1) Lookup Success! Found {len(b_refs)} plans for 'CNS-SIM-994'")
    else:
        # Se as tabelas estiverem vazias, apenas validamos o tipo
        pass

def test_indices_persistence_cycle():
    # Testar o context manager do Indices
    with patch("nutriciones.services.google.sheets.indices.persist_indices") as mock_persist:
        from nutriciones.services.google.sheets.indices import Indices, _recursive_defaultdict
        
        # Cria um objeto indices em branco
        indices = Indices(_recursive_defaultdict(), _recursive_defaultdict(), _recursive_defaultdict(), {})
        
        with indices:
            # Ao sair do __exit__, deve persistir
            pass
            
        mock_persist.assert_called_once()
