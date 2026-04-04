from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class DesfechoClinico(WithPrimaryKeyProperty):
    out_id: PrimaryKey
    pct_id: str
    cns_id: str
    aderencia_autorreferida: int  # 0-10
    objetivo_atingido: bool
    perfil_dominante_na_data: str   # Snapshot do perfil (Triage)
    data_registro: datetime = datetime.now()
