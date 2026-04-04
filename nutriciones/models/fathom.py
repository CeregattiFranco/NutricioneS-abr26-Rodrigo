from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class FathomCall(WithPrimaryKeyProperty):
    fth_id: PrimaryKey
    cns_id: Optional[str] # FK da Consulta (se encontrado)
    fathom_call_id: str # ID externo do Fathom
    summary_status: str # Ex: "ready", "processing"
    transcript_url: str
    processed_at: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
