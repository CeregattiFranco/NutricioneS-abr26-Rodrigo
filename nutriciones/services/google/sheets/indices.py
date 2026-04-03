from collections import defaultdict
from dataclasses import astuple, dataclass
from pathlib import Path
import pickle
from typing import Any, Literal, Sequence

from nutriciones import PROJECT_ROOT, core
from nutriciones.models.agenda import Agenda
from nutriciones.models.consultas import Consulta
from nutriciones.models.pacientes import Paciente, PacienteEmail, PacienteEndereco, PacienteTelefone
from nutriciones.models.planos import PlanoAlimentar
from nutriciones.models.primary_key import HasPrimaryKey
from nutriciones.services import google
from nutriciones.services.google.sheets.types import Either, SheetRange


# helper types to lighten cognitive load
type PrimaryKeyStr = str
type ForeignKeyStr = str
type EmailStr = str
type Sheet = type[HasPrimaryKey]
type SheetColumnStr = str

_cache_file = PROJECT_ROOT / "indices.bin"

_relationships: dict[Sheet, list[tuple[Sheet, SheetColumnStr]]] = {
    Paciente: [],
    PacienteTelefone: [
        (Paciente, "B"),
    ],
    PacienteEmail: [
        (Paciente, "B"),
    ],
    PacienteEndereco: [
        (Paciente, "B"),
    ],
    Agenda: [],
    Consulta: [
        (Paciente, "B"),
        (Agenda, "C")
    ],
    PlanoAlimentar: [
        (Paciente, "B"),
    ],
}


@dataclass(slots=True)
class Indices:
    primary_keys: dict[Sheet, dict[PrimaryKeyStr, SheetRange]]
    foreign_keys: dict[Sheet, dict[PrimaryKeyStr, dict[Sheet, ForeignKeyStr]]]
    foreign_back_references: dict[Sheet, dict[ForeignKeyStr, dict[Sheet, list[PrimaryKeyStr]]]]
    user_emails: dict[EmailStr, PrimaryKeyStr]

    def upsert(self, resource: HasPrimaryKey, range: SheetRange):
        resource_type = type(resource)
        self.primary_keys[resource_type][resource.pk] = range

        if relationships := _relationships[resource_type]:
            # hackish solution, but, contained in here.
            ord_a = ord("A")
            res_tuple = astuple(resource)  # type: ignore

            for rship in relationships:
                index = ord(rship[1]) - ord_a
                fk = res_tuple[index]
                foreign_sheet = rship[0]
                self.foreign_keys[resource_type][resource.pk][foreign_sheet] = fk
                self.foreign_back_references[foreign_sheet][fk][resource_type].append(resource.pk)

        if isinstance(resource, PacienteEmail):
            self.user_emails[resource.email] = resource.pk

    def get_range_from_pk(self, sheet: Sheet, pk: PrimaryKeyStr) -> SheetRange | None:
        return (
            self.primary_keys[sheet][pk]
            if sheet in self.primary_keys
                and pk in self.primary_keys[sheet]
            else None
        )

    def get_fk(self, primary_sheet: Sheet, primary_key: PrimaryKeyStr, foreign_sheet: Sheet) -> ForeignKeyStr | None:
        return (
            self.foreign_keys[primary_sheet][primary_key][foreign_sheet]
            if primary_sheet in self.foreign_keys
                and primary_key in self.foreign_keys[primary_sheet]
                and foreign_sheet in self.foreign_keys[primary_sheet][primary_key]
            else None
        )

    def get_back_references(self, foreign_sheet: Sheet, foreign_key: ForeignKeyStr, primary_sheet: Sheet) -> list[PrimaryKeyStr]:
        return (
            self.foreign_back_references[foreign_sheet][foreign_key][primary_sheet]
            if foreign_sheet in self.foreign_back_references
                and foreign_key in self.foreign_back_references[foreign_sheet]
                and primary_sheet in self.foreign_back_references[foreign_sheet][foreign_key]
            else []
        )

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        persist_indices(self)

_indices: Indices | None = None

def get_indices() -> Indices:
    global _indices

    if _indices is not None:
        return _indices

    if not _cache_file.exists():
        raise FileNotFoundError("indices cache file not found")

    indices: Indices = pickle.loads(_cache_file.read_bytes())  # let it BOOM if error
    _indices = indices
    return _indices


def persist_indices(indices: Indices, target_file: Path = _cache_file):
    with target_file.open('wb') as f:
        pickle.dump(indices, f)


def refresh_indices(sheet_id: str = core.config.GoogleServices.sheet_id_cardapio, *, acknowledge_costly_operation: Literal[True]) -> Indices:
    assert acknowledge_costly_operation is True, "you must acknowledge the cost of this operation."

    new_indices = Indices(_recursive_defaultdict(), _recursive_defaultdict(), _recursive_defaultdict(), {})
    print("[sheet indices] refreshing ALL indices from scratch")

    # Iterate through defined relationships to build the index for each resource type
    for resource_type, relationships in _relationships.items():
        print(f"[sheet indices] processing {resource_type.__name__!r}")
        try:
            last_column = relationships[-1][1] if resource_type is not PacienteEmail else 'C'
        except IndexError:
            last_column = 'A'

        request = google.sheets.PedidoListagemRecursos(
            spreadsheet_id=sheet_id,
            spreadsheet_name=google.sheets.sheet_name_of_resource_type[resource_type],
            spreadsheet_range=f"A2:{last_column}",
            deserialize=_deserialize_id_columns
        )

        resource_list, range = google.sheets.listar_recursos(request)

        # Map each row to its primary key and handle foreign key relationships
        for i, res in enumerate(resource_list, start=range.row_start):
            if res is None:
                print("[sheet indices] 'res' came back as None")
                continue

            (pk, maybe_fk, maybe_fk_or_email) = res

            # Store the exact SheetRange for this primary key for fast O(1) lookups later
            new_indices.primary_keys[resource_type][pk] = SheetRange(range.row(i))
            print(f"[sheet indices][{resource_type.__name__}] indexed {pk=}")

            if maybe_fk is None:
                continue

            fk = maybe_fk

            # Map the primary key to its first foreign key (e.g., PacienteTelefone -> Paciente)
            foreign_sheet = _relationships[resource_type][0][0]
            _index_fk(new_indices, resource_type, pk, foreign_sheet, fk)
            print(f"[sheet indices][{resource_type.__name__}] indexed fk.{foreign_sheet.__name__}={fk!r}")

            if maybe_fk_or_email is not None:
                if resource_type is PacienteEmail:
                    # Special case: map email addresses directly to the primary key for login/lookup
                    email_address = maybe_fk_or_email
                    new_indices.user_emails[email_address] = pk
                    print(f"[sheet indices][{resource_type.__name__}] mapped {email_address!r} -> {pk=}")

                else:
                    # Handle secondary foreign keys (e.g., Consulta -> Agenda)
                    second_fk = maybe_fk_or_email
                    second_foreign_sheet = _relationships[resource_type][1][0]
                    _index_fk(new_indices, resource_type, pk, second_foreign_sheet, second_fk)
                    print(f"[sheet indices][{resource_type.__name__}] indexed fk.{second_foreign_sheet.__name__}={second_fk!r}")

    # Persist the newly built indices to the binary cache file
    global _indices
    _indices = new_indices
    persist_indices(_indices)
    return _indices


def _index_fk(
        indices: Indices,
        primary_sheet: Sheet,
        primary_key: PrimaryKeyStr,
        foreign_sheet: Sheet,
        foreign_key: ForeignKeyStr
    ):
    indices.foreign_keys[primary_sheet][primary_key][foreign_sheet] = foreign_key

    if foreign_key not in indices.foreign_back_references[foreign_sheet]:
        indices.foreign_back_references[foreign_sheet][foreign_key] = defaultdict(list)

    indices.foreign_back_references[foreign_sheet][foreign_key][primary_sheet].append(primary_key)


def _recursive_defaultdict() -> defaultdict[Any, Any]:
    return defaultdict(_recursive_defaultdict)


def _deserialize_id_columns(row: Sequence[str]) -> Either[tuple[PrimaryKeyStr, ForeignKeyStr | None, str | None], None]:
    assert 1 <= len(row) <= 3
    return (
            row[0],
            row[1] if len(row) >= 2 else None,
            row[2] if len(row) == 3 else None
        ), None
