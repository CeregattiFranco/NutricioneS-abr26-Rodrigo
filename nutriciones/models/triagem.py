from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class TriagemPaciente(WithPrimaryKeyProperty):
    tri_id: PrimaryKey
    pct_id: str
    escore_metabolico: int      # 0-15
    escore_emocional: int       # 0-15
    escore_custo_energia: int   # 0-15
    escore_urgencia: int        # 0-15
    escore_seguranca: int       # 0-15
    perfil_dominante: str       # Cor ou Nome do Bloco
    data_triagem: datetime = datetime.now()
