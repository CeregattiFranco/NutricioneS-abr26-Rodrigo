from dataclasses import astuple
from datetime import date, datetime
from typing import Sequence
import json

from nutriciones.models.pacientes import Paciente, PacienteEmail, PacienteEndereco, PacienteTelefone
from nutriciones.models.agenda import Agenda
from nutriciones.models.consultas import Consulta
from nutriciones.services.google.sheets.types import Either

def _parse_date(val: str) -> date:
    try:
        return datetime.fromisoformat(val).date() if 'T' in val else datetime.strptime(val, "%Y-%m-%d").date()
    except:
        return date.today()

def _parse_datetime(val: str) -> datetime:
    try:
        return datetime.fromisoformat(val)
    except:
        return datetime.now()

def serialize_paciente(p: Paciente) -> Sequence[str]:
    return [str(v) if not isinstance(v, (date, datetime)) else v.isoformat() for v in astuple(p)]

def deserialize_paciente(row: Sequence[str]) -> Either[Paciente, ValueError]:
    try:
        return Paciente(
            pct_id=row[0],
            nome=row[1],
            sobrenome=row[2],
            cpf=row[3],
            data_nascimento=_parse_date(row[4]),
            responsavel_id=row[5],
            status=row[6],
            origem=row[7],
            ativo=row[8] == 'TRUE',
            created_at=_parse_datetime(row[9]),
            updated_at=_parse_datetime(row[10])
        ), None
    except Exception as e:
        return None, ValueError(f"failed to deserialize paciente: {e}")

def deserialize_telefone(row: Sequence[str]) -> Either[PacienteTelefone, ValueError]:
    try:
        return PacienteTelefone(
            tel_id=row[0], pct_id=row[1], ddi=row[2], ddd=row[3],
            telefone=row[4], whatsapp=row[5] == 'TRUE',
            contato_principal=row[6] == 'TRUE', ativo=row[7] == 'TRUE',
            created_at=_parse_datetime(row[8]), updated_at=_parse_datetime(row[9])
        ), None
    except Exception as e: return None, ValueError(str(e))

def deserialize_email(row: Sequence[str]) -> Either[PacienteEmail, ValueError]:
    try:
        return PacienteEmail(
            mail_id=row[0], pct_id=row[1], email=row[2], validado=row[3] == 'TRUE',
            opt_in_data=row[4] if row[4] == '' else _parse_datetime(row[4]),
            email_principal=row[5] == 'TRUE', ativo=row[6] == 'TRUE',
            created_at=_parse_datetime(row[7]), updated_at=_parse_datetime(row[8])
        ), None
    except Exception as e: return None, ValueError(str(e))

def deserialize_endereco(row: Sequence[str]) -> Either[PacienteEndereco, ValueError]:
    try:
        return PacienteEndereco(
            adr_id=row[0], pct_id=row[1], cep=row[2], logradouro=row[3],
            numero=row[4], complemento=row[5], bairro=row[6], cidade=row[7],
            uf=row[8], pais=row[9], endereco_nfse=row[10] == 'TRUE',
            ativo=row[11] == 'TRUE', created_at=_parse_datetime(row[12]), updated_at=_parse_datetime(row[13])
        ), None
    except Exception as e: return None, ValueError(str(e))

def deserialize_consulta(row: Sequence[str]) -> Either[Consulta, ValueError]:
    try:
        return Consulta(
            cns_id=row[0], pct_id=row[1], agd_id=row[2], consulta_perfil=row[3],
            status=row[4], ativo=row[5] == 'TRUE', slot=row[6],
            calendar_event_id=row[7], meet_url=row[8], calendar_event_url=row[9],
            created_at=_parse_datetime(row[10]), updated_at=_parse_datetime(row[11])
        ), None
    except Exception as e: return None, ValueError(str(e))
