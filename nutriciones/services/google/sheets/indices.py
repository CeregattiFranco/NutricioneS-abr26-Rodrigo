from collections import defaultdict
from dataclasses import astuple, dataclass
import json
import redis
from typing import Any, Literal, Sequence, Optional

from nutriciones import PROJECT_ROOT, core
from nutriciones.models.agenda import Agenda
from nutriciones.models.consultas import Consulta
from nutriciones.models.pacientes import Paciente, PacienteEmail, PacienteEndereco, PacienteTelefone
from nutriciones.models.planos import PlanoAlimentar
from nutriciones.models.prontuario import Prontuario
from nutriciones.models.mensagens import Mensagem
from nutriciones.models.biometria import ExameLaboratorial
from nutriciones.models.rascunhos import RascunhoClinico
from nutriciones.models.primary_key import HasPrimaryKey
from nutriciones.services import google
from nutriciones.services.google.sheets.types import Either, SheetRange

logger = core.get_base_logger("NSS-INDICES")

# helper types
type PrimaryKeyStr = str
type ForeignKeyStr = str
type EmailStr = str
type Sheet = type[HasPrimaryKey]
type SheetColumnStr = str

_relationships: dict[Sheet, list[tuple[Sheet, SheetColumnStr]]] = {
    Paciente: [],
    PacienteTelefone: [(Paciente, "B")],
    PacienteEmail: [(Paciente, "B")],
    PacienteEndereco: [(Paciente, "B")],
    Agenda: [],
    Consulta: [(Paciente, "B"), (Agenda, "C")],
    PlanoAlimentar: [(Paciente, "B")],
    Prontuario: [(Paciente, "C"), (Consulta, "B")],
    Mensagem: [(Paciente, "B")],
    ExameLaboratorial: [(Paciente, "B")],
    RascunhoClinico: [(Paciente, "C"), (Consulta, "B")],
}

class IndicesStateless:
    """Implementação Stateless do Cache de Índices via Redis (Fator VI)."""
    def __init__(self):
        self.redis_client = None
        try:
            self.redis_client = redis.from_url(core.config.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info("Conectado ao Redis com Sucesso (Stateless Mode).")
        except Exception as e:
            logger.warning(f"Falha ao conectar no Redis ({e}). Usando modo Local In-Memory (Stateful).")
            self.redis_client = None

        # Fallback local para Graceful Degradation
        self._local_pk = defaultdict(dict)
        self._local_fk = defaultdict(lambda: defaultdict(dict))
        self._local_back = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self._local_emails = {}

    def _key(self, sheet: Sheet, pk: str = "") -> str:
        return f"nss:idx:{sheet.__name__}:{pk}"

    def upsert(self, resource: HasPrimaryKey, range: SheetRange):
        sheet = type(resource)
        pk = resource.pk
        
        if self.redis_client:
            self.redis_client.hset(self._key(sheet), pk, range.raw)
        self._local_pk[sheet][pk] = range

        if relationships := _relationships[sheet]:
            ord_a = ord("A")
            res_tuple = astuple(resource)
            for rship in relationships:
                index = ord(rship[1]) - ord_a
                fk = res_tuple[index]
                foreign_sheet = rship[0]
                
                if self.redis_client:
                    # FK mapping
                    self.redis_client.hset(f"{self._key(sheet, pk)}:fk", foreign_sheet.__name__, fk)
                    # Back-reference (List)
                    back_key = f"nss:back:{foreign_sheet.__name__}:{fk}:{sheet.__name__}"
                    self.redis_client.sadd(back_key, pk)
                
                self._local_fk[sheet][pk][foreign_sheet] = fk
                self._local_back[foreign_sheet][fk][sheet].append(pk)

        if isinstance(resource, PacienteEmail):
            if self.redis_client:
                self.redis_client.hset("nss:emails", resource.email, pk)
            self._local_emails[resource.email] = pk

    def get_range_from_pk(self, sheet: Sheet, pk: PrimaryKeyStr) -> Optional[SheetRange]:
        if self.redis_client:
            raw = self.redis_client.hget(self._key(sheet), pk)
            return SheetRange(raw) if raw else None
        return self._local_pk[sheet].get(pk)

    def get_fk(self, primary_sheet: Sheet, primary_key: PrimaryKeyStr, foreign_sheet: Sheet) -> Optional[ForeignKeyStr]:
        if self.redis_client:
            return self.redis_client.hget(f"{self._key(primary_sheet, primary_key)}:fk", foreign_sheet.__name__)
        return self._local_fk[primary_sheet][primary_key].get(foreign_sheet)

    def get_back_references(self, foreign_sheet: Sheet, foreign_key: ForeignKeyStr, primary_sheet: Sheet) -> list[PrimaryKeyStr]:
        if self.redis_client:
            back_key = f"nss:back:{foreign_sheet.__name__}:{foreign_key}:{primary_sheet.__name__}"
            return list(self.redis_client.smembers(back_key))
        return self._local_back[foreign_sheet][foreign_key].get(primary_sheet, [])

    @property
    def user_emails(self):
        if self.redis_client:
            return self.redis_client.hgetall("nss:emails")
        return self._local_emails

    def __enter__(self): return self
    def __exit__(self, *args): pass

_indices_stateless: IndicesStateless | None = None

def get_indices() -> IndicesStateless:
    global _indices_stateless
    if _indices_stateless is None:
        _indices_stateless = IndicesStateless()
    return _indices_stateless

def refresh_indices(sheet_id: str = core.config.GoogleServices.sheet_id_cardapio, *, acknowledge_costly_operation: Literal[True]) -> IndicesStateless:
    assert acknowledge_costly_operation is True
    indices = get_indices()
    
    if indices.redis_client:
        logger.info("[NSS-INDICES] Limpando cache Redis para refresh total.")
        keys = indices.redis_client.keys("nss:*")
        if keys: indices.redis_client.delete(*keys)

    logger.info("[NSS-INDICES] Refreshing ALL indices from SSoT Sheets...")
    
    for resource_type in _relationships:
        from nutriciones.services.google.sheets import types, base
        from nutriciones.services.google.sheets.serializers.paciente import (
            deserialize_paciente, deserialize_telefone, deserialize_email, 
            deserialize_endereco, deserialize_consulta, deserialize_mensagem,
            deserialize_prontuario
        )
        from nutriciones.services.google.sheets.serializers.dieta import deserialize_plano

        serializers = {
            Paciente: deserialize_paciente, PacienteTelefone: deserialize_telefone,
            PacienteEmail: deserialize_email, PacienteEndereco: deserialize_endereco,
            Consulta: deserialize_consulta, PlanoAlimentar: deserialize_plano,
            Prontuario: deserialize_prontuario, Mensagem: deserialize_mensagem,
            Agenda: lambda r: (Agenda(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]), None) # placeholder logic
        }

        request = types.PedidoListagemRecursos(
            spreadsheet_id=sheet_id,
            spreadsheet_name=base.sheet_name_of_resource_type[resource_type],
            spreadsheet_range="A2:Z",
            deserialize=serializers.get(resource_type, lambda r: (None, ValueError("No serializer")))
        )

        try:
            resources, range = base.listar_recursos(request)
            for i, res in enumerate(resources, start=range.row_start):
                if res: indices.upsert(res, SheetRange(range.row(i)))
                logger.info(f"Indexed {resource_type.__name__}: {res.pk if res else 'None'}")
        except Exception as e:
            logger.error(f"Erro ao indexar {resource_type.__name__}: {e}")

    logger.info("[✔] NSS-INDICES: Boot completo. Telemetria Ativa.")
    return indices

def _deserialize_id_columns(row: Sequence[str]) -> Either[tuple[PrimaryKeyStr, ForeignKeyStr | None, str | None], None]:
    return (row[0], row[1] if len(row) >= 2 else None, row[2] if len(row) == 3 else None), None
