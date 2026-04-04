import pytest
from fastapi.testclient import TestClient
from main_api import app
import hashlib
import hmac
import json
from nutriciones.core import config

client = TestClient(app)

def test_health_check():
    """Valida se o sistema está saudável."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_webhook_ocr_exames(mock_google_sheets):
    """Teste de ingestão de exames Vision (OCR)."""
    exames_data = [
        {
            "pct_id": "PCT-TEST-01",
            "parametro": "Ferritina",
            "valor": 12.0,
            "unidade": "ng/mL",
            "ref_min": 30.0,
            "ref_max": 400.0
        }
    ]
    response = client.post("/webhook/n8n/exames", json=exames_data)
    assert response.status_code == 200
    assert response.json()["ingested"] == 1

def test_secure_fathom_webhook_invalid_signature():
    """Garante que webhooks sem assinatura válida são rejeitados."""
    payload = {"call_id": "test_id"}
    response = client.post(
        "/webhook/fathom", 
        json=payload,
        headers={"X-Fathom-Signature": "wrong-one"}
    )
    assert response.status_code == 401

def test_secure_fathom_webhook_valid_signature(mocker, mock_google_sheets):
    """Garante que webhooks com assinatura válida são aceitos (NSS Listen)."""
    payload = {"call_id": "test_id_123"}
    payload_bytes = json.dumps(payload).encode()
    
    # Gerar assinatura válida para o teste usando o secret mockado
    mocker.patch("nutriciones.core.Config.FATHOM_WEBHOOK_SECRET", "test-secret")
    config.FATHOM_WEBHOOK_SECRET = "test-secret"
    
    signature = hmac.new(
        b"test-secret",
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    response = client.post(
        "/webhook/fathom", 
        json=payload,
        headers={"X-Fathom-Signature": signature}
    )
    assert response.status_code == 200 # No código atual, enviamos 200 e recebemos 202 Accepted via background
    assert response.json()["status"] == "accepted"
