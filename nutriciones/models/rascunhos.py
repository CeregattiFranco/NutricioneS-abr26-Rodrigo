from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class RascunhoClinico(WithPrimaryKeyProperty):
    ras_id: PrimaryKey
    cns_id: str         # Relacionamento com a Consulta
    pct_id: str
    objetivo_sugerido: str
    diagnostico_sugerido: str
    conduta_sugerida: str
    orientacao_sugerida: str
    fonte: str          # Ex: "Fathom AI"
    status: str = "pendente" # pendente, aprovado, rejeitado
    created_at: datetime = datetime.now()
