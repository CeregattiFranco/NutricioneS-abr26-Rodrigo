import pytest
from fastapi.testclient import TestClient
from main_api import app
from nutriciones.services.triagem_service import calcular_escores_triagem

client = TestClient(app)

def test_calculo_escores_vermelho():
    """Valida se o cálculo gera perfil Vermelho quando scores são altos."""
    respostas = {f"c{i}": 3 for i in range(1, 4)} # Custo Energia máximo
    resultado = calcular_escores_triagem("PCT-01", respostas)
    assert "VERMELHO_CustoEnergia" == resultado.perfil_dominante

def test_calculo_escores_verde():
    """Valida se o cálculo gera perfil Verde quando scores são baixos."""
    respostas = {f"m{i}": 1 for i in range(1, 4)}
    resultado = calcular_escores_triagem("PCT-01", respostas)
    assert "VERDE_ESTAVEL" == resultado.perfil_dominante

def test_webhook_triagem_pipeline(mock_google_sheets):
    """Teste de integração do Webhook de Triagem."""
    payload = {
        "pct_id": "PCT-TRI-01",
        "respostas": {"m1": 3, "m2": 3, "m3": 3}
    }
    response = client.post("/webhook/forms/triagem", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
