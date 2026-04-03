from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty


@dataclass(frozen=True)
class Consulta(WithPrimaryKeyProperty):
    cns_id: PrimaryKey
    pct_id: str
    agd_id: str
    consulta_perfil: Literal['adulto','gestante','lactante','introducao_alimentar','menopausa']
    status: Literal['livre', 'agendado', 'confirmado', 'realizado', 'cancelado', 'no_show']
    ativo: bool
    slot: Literal['primeira_vez', 'retorno']
    calendar_event_id: str
    meet_url: str
    calendar_event_url: str
    created_at: datetime
    updated_at: datetime
