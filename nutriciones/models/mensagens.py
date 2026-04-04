from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass(frozen=True)
class Mensagem(WithPrimaryKeyProperty):
    msg_id: PrimaryKey
    pct_id: str
    origem: Literal['email', 'whatsapp', 'agenda', 'follow-up', 'campanha']
    assunto: str
    conteudo: str
    resumo_ia: str
    status: Literal['pendente', 'lida', 'respondida', 'arquivada', 'agendado', 'enviado']
    template_name: str = ""
    scheduled_at: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
