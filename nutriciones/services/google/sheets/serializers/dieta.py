from dataclasses import astuple
from typing import Sequence

from nutriciones.models.planos import PlanoAlimentar
from nutriciones.services.google.sheets.types import Either


def serialize_plano(plano: PlanoAlimentar) -> Sequence[str]:
    # format the fields as strings
    return [str(v) for v in astuple(plano)]


def deserialize_plano(row: Sequence[str]) -> Either[PlanoAlimentar, ValueError]:
    try:
        if len(row) < 9:
            return None, ValueError("row does not contain all required columns")

        plano = PlanoAlimentar(
            plano_id=row[0],
            pct_id=row[1],
            cns_id=row[2] if row[2] else None,
            data=row[3],
            total_kcal=float(row[4]),
            total_proteina=float(row[5]),
            total_carboidrato=float(row[6]),
            total_lipidios=float(row[7]),
            itens_detalhados=row[8]
        )
        return plano, None
    except Exception as e:
        return None, ValueError(f"failed to deserialize plano: {e}")
