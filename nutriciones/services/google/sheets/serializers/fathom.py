import logging
from typing import Sequence, Optional
from datetime import datetime

from nutriciones.models.fathom import FathomCall
from nutriciones.services.google.sheets.types import Either

def _parse_datetime(dt_str: str) -> datetime:
    try: return datetime.fromisoformat(dt_str)
    except: return datetime.now()

def serialize_fathom_call(call: FathomCall) -> Sequence[str]:
    return [
        call.fth_id,
        call.cns_id or "",
        call.fathom_call_id,
        call.summary_status,
        call.transcript_url,
        call.processed_at.isoformat() if call.processed_at else "",
        call.created_at.isoformat(),
        call.updated_at.isoformat()
    ]

def deserialize_fathom_call(row: Sequence[str]) -> Either[FathomCall, ValueError]:
    try:
        return FathomCall(
            fth_id=row[0],
            cns_id=row[1] if row[1] else None,
            fathom_call_id=row[2],
            summary_status=row[3],
            transcript_url=row[4],
            processed_at=_parse_datetime(row[5]) if row[5] else None,
            created_at=_parse_datetime(row[6]),
            updated_at=_parse_datetime(row[7])
        ), None
    except Exception as e:
        return None, ValueError(str(e))
