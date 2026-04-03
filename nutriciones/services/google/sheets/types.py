from dataclasses import dataclass, field
import re
from typing import Callable, Sequence


# Pythonic-ish way to represent a functional type
type Either[T, E] = tuple[T, None] | tuple[None, E]


@dataclass(frozen=True)
class SheetsRequestBase:
    spreadsheet_id: str
    spreadsheet_name: str


@dataclass(frozen=True)
class PedidoListagemRecursos[R](SheetsRequestBase):
    spreadsheet_range: str
    deserialize: Callable[[Sequence[str]], Either[R, ValueError]]


@dataclass(frozen=True)
class PedidoInsercaoRecurso[R](SheetsRequestBase):
    recurso: R
    serialize: Callable[[R], Sequence[str]]


@dataclass(frozen=True)
class PedidoInsercaoListaRecursos[R](SheetsRequestBase):
    recursos: list[R]
    serialize: Callable[[R], Sequence[str]]


@dataclass(frozen=True)
class PedidoAtualizacaoRecurso[R](SheetsRequestBase):
    spreadsheet_range: str
    recurso: R
    serialize: Callable[[R], Sequence[str]]


# sheet_name!A1:Z1000
_a1_notation_pattern = re.compile(
    r"^(?P<sheet_name>[a-z_]+)"
    r"!(?P<column_start>[A-Z]+)(?P<row_start>\d+)"  # range start
    r":(?P<column_end>[A-Z]+)(?P<row_end>\d*)$"  # range end
)

@dataclass(frozen=True)
class SheetRange:
    raw: str
    sheet_name: str = field(init=False)
    column_start: str = field(init=False)
    row_start: int = field(init=False)
    column_end: str = field(init=False)
    row_end: int | None = field(init=False)

    def __post_init__(self):
        if not (match := _a1_notation_pattern.match(self.raw)):
            raise ValueError("range inválido")

        object.__setattr__(self, "sheet_name", match.group('sheet_name'))
        object.__setattr__(self, "column_start", match.group('column_start'))
        object.__setattr__(self, "row_start", int(match.group('row_start')))
        object.__setattr__(self, "column_end", match.group('column_end'))
        object.__setattr__(self, "row_end", int(match.group('row_end')) if match.group('row_end') else None)

    def row(self, row_num: int, /):
        if not (
                self.row_end
                and self.row_start <= row_num <= self.row_end
                or self.row_start <= row_num
            ):
            raise ValueError("row_num must be within the range")

        return f"{self.sheet_name}!{self.column_start}{row_num}:{self.column_end}{row_num}"

    def last_row(self) -> str | None:
        return f"{self.sheet_name}!{self.column_start}{self.row_end}:{self.column_end}{self.row_end}" if self.row_end else None
