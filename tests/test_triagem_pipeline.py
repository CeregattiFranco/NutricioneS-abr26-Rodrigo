import pytest
from fastapi.testclient import TestClient
from main_api import app
from nutriciones.services.triagem_service import processar_respostas_triage

client = TestClient(app)

def test_calculo_escores_vermelho_execucao():
    """Valida se o cálculo gera perfil Vermelho quando scores de execução são altos."""
    respostas = {f"e{i}": 3 for i in range(1, 4)} # Execução máximo
    resultado = processar_respostas_triage("PCT-01", respostas)
    assert "VERMELHO_EXECUCAO" == resultado.dominante_sugerido

def test_webhook_triagem_pipeline(mock_google_sheets):
    """Teste de integração do Webhook de Triagem com Token."""
    payload = {
        "pct_id": "PCT-TRI-01",
        "respostas": {"m1": 3, "m2": 3, "m3": 3},
        "nss_forms_token": "nss_secret_123"
    }
    response = client.post("/webhook/forms/triagem", json=payload)
    assert response.status_code == 200
