from dataclasses import astuple
from typing import Sequence
from nutriciones.models.fathom import FathomCall
from nutriciones.services.google.sheets.types import Either

def serialize_fathom_call(call: FathomCall) -> list:
    """Converte um objeto FathomCall em uma linha para o Google Sheets (40 colunas)."""
    return list(astuple(call))

def deserialize_fathom_call(row: Sequence[str]) -> Either[FathomCall, Exception]:
    """Converte uma linha do Google Sheets em um objeto FathomCall."""
    try:
        # Preenche com strings vazias se o Sheets omitiu colunas em branco no final
        row_list = list(row)
        while len(row_list) < 40:
            row_list.append("")
        
        return FathomCall(*row_list[:40]), None
    except Exception as e:
        return None, e
