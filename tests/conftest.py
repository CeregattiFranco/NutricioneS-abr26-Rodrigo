import pytest
from fakeredis import FakeRedis
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    """Substitui o Redis por um FakeRedis em todos os testes."""
    fake_r = FakeRedis(decode_responses=True)
    mocker.patch("redis.from_url", return_value=fake_r)
    return fake_r

@pytest.fixture
def mock_google_sheets(mocker):
    """Mock total do SSoT para evitar escritas reais."""
    mock_base = mocker.patch("nutriciones.services.google.sheets.base.inserir_lista_recursos")
    mock_list = mocker.patch("nutriciones.services.google.sheets.base.listar_recursos")
    return mock_base, mock_list

@pytest.fixture
def mock_fathom_api(mocker):
    """Mock do cliente Fathom."""
    mock_client = mocker.patch("nutriciones.services.fathom_service.FathomClient.buscar_detalhes_chamada")
    mock_client.return_value = {
        "call_id": "test_call_123",
        "transcript_summary": "Paciente teste com objetivos X."
    }
    return mock_client

@pytest.fixture
def mock_chromadb(mocker):
    """Mock da memória vetorial (NSS Oracle)."""
    return mocker.patch("nutriciones.services.memory.embeddings.ClinicalMemory")
