from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class Prontuario(WithPrimaryKeyProperty):
    prt_id: PrimaryKey
    cns_id: str
    pct_id: str
    objetivo: str
    diagnostico: str
    conduta: str
    orientacao: str
    created_at: datetime
    updated_at: datetime
