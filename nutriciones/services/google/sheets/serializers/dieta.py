from dataclasses import astuple
from typing import Sequence

from nutriciones.models.planos import PlanoAlimentar
from nutriciones.services.google.sheets.types import Either


def serialize_plano(plano: PlanoAlimentar) -> Sequence[str]:
    # format the fields as strings
    return [str(v) for v in astuple(plano)]


def deserialize_plano(row: Sequence[str]) -> Either[PlanoAlimentar, ValueError]:
    try:
        if len(row) < 8:
            return None, ValueError("row does not contain all required columns")

        plano = PlanoAlimentar(
            plano_id=row[0],
            pct_id=row[1],
            data=row[2],
            total_kcal=float(row[3]),
            total_proteina=float(row[4]),
            total_carboidrato=float(row[5]),
            total_lipidios=float(row[6]),
            itens_detalhados=row[7]
        )
        return plano, None
    except Exception as e:
        return None, ValueError(f"failed to deserialize plano: {e}")
