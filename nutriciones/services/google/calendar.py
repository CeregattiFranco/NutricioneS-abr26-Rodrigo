from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal, TypedDict
import uuid

from nutriciones.services.google.auth_service import get_creds
from googleapiclient.discovery import build


@dataclass(frozen=True)
class NovoEvento:
    calendar_id: str
    summary: str
    description: str
    start: datetime
    end: datetime
    attendees: list[Convidado] = field(default_factory=list)

    def __post_init__(self):
        assert self.end > self.start


class Convidado(TypedDict):
    email: str
    response: Literal['needsAction', 'accepted']


def criar_evento(evento: NovoEvento) -> tuple[str, str, str]:
    """Retorna event_id, event_url, e meet_url"""
    # Usando a construção direta já que base.py de rebirth foi substituido por auth_service
    creds = get_creds()
    service = build('calendar', 'v3', credentials=creds)
    
    event_body = asdict(evento)
    event_body['start'] = {'dateTime': evento.start.isoformat()}
    event_body['end'] = {'dateTime': evento.end.isoformat()}
    calendar_id: str = event_body.pop('calendar_id')

    # Requisitando link do Google Meet
    event_body['conferenceData'] = {
        'createRequest': {
            'requestId': uuid.uuid4().hex,
            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
        }
    }

    created_event = service.events().insert(
        calendarId=calendar_id, 
        body=event_body,
        conferenceDataVersion=1  # Requerido pro Meet
    ).execute()

    event_id: str = created_event['id']
    event_url: str = created_event['htmlLink']
    
    meet_url = ""
    # Extract meet URL
    if 'conferenceData' in created_event:
        for entryPoint in created_event['conferenceData'].get('entryPoints', []):
            if entryPoint['entryPointType'] == 'video':
                meet_url = entryPoint['uri']

    return event_id, event_url, meet_url
