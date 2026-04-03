import pytest
from nutriciones.services.sqlite import get_alimento_exato
from nutriciones.models.planos import ItemRefeicaoInput, PlanoAlimentar
from nutriciones.services.dieta_service import calcular_refeicao, salvar_plano_alimentar
from unittest.mock import patch

def test_sqlite_taco_retrieval():
    # Execute - Alimento base da TACO
    # Testamos com um conhecido que sabemos que está lá
    alimento = get_alimento_exato("alface, americana, crua")
    
    # Assert
    assert alimento is not None
    assert alimento.nome == "Alface, americana, crua"
    assert alimento.kcal > 0 # Proteção básica

def test_calcular_refeicao_logic():
    # Setup
    itens = [
        ItemRefeicaoInput(nome="Alface, americana, crua", peso_g=100.0)
    ]
    
    # Execute
    resultado = calcular_refeicao(itens)
    
    # Assert
    assert resultado.kcal > 0
    assert len(resultado.itens_analisados) == 1
    assert resultado.itens_analisados[0].nome == "Alface, americana, crua"

@patch("nutriciones.services.dieta_service.inserir_lista_recursos")
def test_salvar_plote_7_dias(mock_insert):
    # Setup
    planos = [
        PlanoAlimentar(
            plano_id=f"plano_{i}",
            pct_id="pct_001",
            data=f"Dia {i}",
            total_kcal=1800.0,
            total_proteina=70,
            total_carboidrato=200,
            total_lipidios=40,
            itens_detalhados="[]"
        ) for i in range(7)
    ]
    
    # Execute
    salvar_plano_alimentar(planos)
    
    # Assert
    mock_insert.assert_called_once()
    args, _ = mock_insert.call_args
    pedido = args[0]
    assert len(pedido.recursos) == 7
    assert pedido.recursos[0].plano_id == "plano_0"
    assert pedido.recursos[6].plano_id == "plano_6"
