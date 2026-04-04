import pytest
from fastapi.testclient import TestClient
from main_api import app
from nutriciones.services.analytics import nss_analytics

client = TestClient(app)

def test_analytics_performance_endpoint():
    """Valida se o endpoint de auditoria retorna os dados de correlação."""
    response = client.get("/clinica/analytics")
    assert response.status_code == 200
    assert "correlacao_perfil_vermelho_sucesso" in response.json()["stats"]
    assert response.json()["stats"]["correlacao_perfil_vermelho_sucesso"] > 0.8

def test_ltv_calculation():
    """Valida o cálculo de LTV de um paciente."""
    res = nss_analytics.avaliar_ltv_paciente("PCT-01")
    assert res["consultas_realizadas"] == 4
    assert res["score_aderencia_medio"] >= 8.0
