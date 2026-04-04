import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from nutriciones.services.pacientes import embarcar_paciente
from nutriciones.models.pacientes import Paciente

@patch("nutriciones.services.pacientes.inserir_lista_recursos")
@patch("nutriciones.services.pacientes.find_patient_folder")
def test_embarque_paciente_flow(mock_find, mock_insert):
    # Setup
    mock_find.return_value = "folder_123"
    
    # Execute
    pct_id = embarcar_paciente(
        nome="Teste",
        sobrenome="Workflow",
        cpf="00011122233",
        data_nascimento=date(1990, 1, 1),
        telefone="11999998888",
        email="teste@workflow.com",
        logradouro="Rua Teste",
        numero="123",
        cep="00000-000",
        bairro="Centro",
        cidade="Sampa",
        uf="SP"
    )
    
    # Assert
    assert pct_id is not None
    assert mock_insert.call_count == 4 # Paciente, Telefone, Email, Endereco
    mock_find.assert_called_once_with(pct_id, nome="Teste", sobrenome="Workflow")
    
    # Verifica se o primeiro insert foi o do Paciente
    args, kwargs = mock_insert.call_args_list[0]
    pedido = args[0]
    assert pedido.recursos[0].nome == "Teste"
    assert pedido.recursos[0].pct_id == pct_id
