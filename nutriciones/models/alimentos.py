from dataclasses import dataclass

@dataclass
class AlimentoSQLite:
    nome: str
    kcal: float
    proteina_g: float
    lipidios_g: float
    carboidratos_g: float
