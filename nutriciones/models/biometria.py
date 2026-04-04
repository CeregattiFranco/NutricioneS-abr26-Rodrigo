from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class ExameLaboratorial(WithPrimaryKeyProperty):
    exm_id: PrimaryKey
    pct_id: str
    parametro: str      # Ex: Vitamina D, Ferritina, Glicose
    valor: float
    unidade: str        # Ex: ng/mL, mg/dL
    referencia_min: float
    referencia_max: float
    observacao: Optional[str] = None
    data_exame: datetime = datetime.now()
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
