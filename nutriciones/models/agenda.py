from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Literal

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty


@dataclass(frozen=True)
class Agenda(WithPrimaryKeyProperty):
    agd_id: PrimaryKey
    data: date
    hora_inicio: time
    hora_fim: time
    # timezone: str
    slot: Literal['consulta', 'reuniao', 'aula']
    status: Literal['livre', 'preenchido']
    ativo: bool
    # profissional_id: str
    created_at: str
    updated_at: str

    def get_datahora_inicio(self):
        return datetime.combine(self.data, self.hora_inicio).astimezone()

    def get_datahora_fim(self):
        return datetime.combine(self.data, self.hora_fim).astimezone()
