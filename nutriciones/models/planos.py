from dataclasses import dataclass
from nutriciones.models.primary_key import PrimaryKey, WithPrimaryKeyProperty

@dataclass
class PlanoAlimentar(WithPrimaryKeyProperty):
    plano_id: PrimaryKey
    pct_id: str
    data: str
    total_kcal: float
    total_proteina: float
    total_carboidrato: float
    total_lipidios: float
    itens_detalhados: str # Formatado em texto/JSON

@dataclass
class ItemRefeicaoInput:
    nome: str
    peso_g: float

@dataclass
class MacroResult:
    nome: str
    peso_g: float
    kcal: float
    proteina_g: float
    lipidios_g: float
    carboidratos_g: float

@dataclass
class TotaisRefeicao:
    kcal: float
    proteina_g: float
    lipidios_g: float
    carboidratos_g: float
    itens_analisados: list[MacroResult]
    nao_encontrados: list[str]
