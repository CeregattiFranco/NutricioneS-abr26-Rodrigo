from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class TriagemPerfil(WithPrimaryKeyProperty):
    tri_id: PrimaryKey
    pct_id: str
    score_metabolico: int      # 0-3 por questão
    score_comportamental: int
    score_execucao: int
    score_expectativa: int
    score_seguranca: int
    dominante_sugerido: str   # Bloco com maior pontuação
    data_triagem: datetime = datetime.now()
