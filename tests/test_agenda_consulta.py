import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from nutriciones.services.consultas import agendar_consulta

@patch("nutriciones.services.consultas.criar_evento")
@patch("nutriciones.services.consultas.inserir_recurso")
def test_agendar_consulta_flow(mock_insert, mock_calendar):
    # Setup
    mock_calendar.return_value = ("evt_123", "http://calendar/123", "https://meet.google.com/abc-defg-hij")
    
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=1)
    
    # Execute
    res = agendar_consulta(
        pct_id="paciente-mock",
        agd_id="agenda-mock",
        start=start,
        end=end
    )
    
    # Assert
    assert res["meet_url"] == "https://meet.google.com/abc-defg-hij"
    assert res["event_id"] == "evt_123"
    
    mock_calendar.assert_called_once()
    mock_insert.assert_called_once()
    
    # Verifica dados inseridos no Sheets
    args, _ = mock_insert.call_args
    consulta_inserida = args[0].recurso
    assert consulta_inserida.pct_id == "paciente-mock"
    assert consulta_inserida.agd_id == "agenda-mock"
    assert consulta_inserida.meet_url == "https://meet.google.com/abc-defg-hij"
