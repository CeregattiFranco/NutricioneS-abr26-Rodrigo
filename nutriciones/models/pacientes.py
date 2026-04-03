from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

from nutriciones.models.base import EmptyStr
from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty


@dataclass(frozen=True)
class Paciente(WithPrimaryKeyProperty):
    pct_id: PrimaryKey
    nome: str
    sobrenome: str
    cpf: str
    data_nascimento: date
    responsavel_id: str | EmptyStr
    status: Literal['lead', 'ativo', 'inativo', 'bloqueado', 'responsável']
    origem: str | EmptyStr = ''
    ativo: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_underage(self) -> bool:
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year

        maior_de_idade = (
            (hoje - self.data_nascimento.replace(year=hoje.year)).days <= 0
            if idade == 18
            else idade > 18
        )

        return (
            self.responsavel_id != ''
            and maior_de_idade
        )

@dataclass(frozen=True)
class PacienteTelefone(WithPrimaryKeyProperty):
    tel_id: PrimaryKey
    pct_id: str
    ddi: str
    ddd: str
    telefone: str
    whatsapp: bool
    contato_principal: bool
    ativo: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PacienteEmail(WithPrimaryKeyProperty):
    mail_id: PrimaryKey
    pct_id: str
    email: str
    validado: bool
    opt_in_data: datetime | EmptyStr
    email_principal: bool
    ativo: bool
    created_at: datetime
    updated_at: datetime

    def is_opted_in(self):
        return self.opt_in_data != ''


@dataclass(frozen=True)
class PacienteEndereco(WithPrimaryKeyProperty):
    adr_id: PrimaryKey
    pct_id: str
    cep: str
    logradouro: str
    numero: str
    complemento: str | EmptyStr
    bairro: str
    cidade: str
    uf: str
    pais: str
    endereco_nfse: bool
    ativo: bool
    created_at: datetime
    updated_at: datetime
