import sys
import json
import logging
from dataclasses import dataclass, astuple
from pathlib import Path

# Padrão PathLib da Rebirth
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.core import config
from nutriciones.services.sqlite import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlimentoSQLiteBulk:
    nome: str
    kcal: float
    proteina_g: float
    lipidios_g: float
    carboidratos_g: float

def extract_nutrient_value(val) -> float:
    if not val or val == 'NA' or val == '*':
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def load_taco_data_from_file() -> list:
    logger.info(f"Carregando dados JSON via PathLib: {config.TACO_JSON_PATH}")
    if not config.TACO_JSON_PATH.exists():
        logger.error(f"Arquivo não encontrado: {config.TACO_JSON_PATH}")
        sys.exit(1)
        
    with open(config.TACO_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def transform_food_data(json_data: list) -> list[AlimentoSQLiteBulk]:
    alimentos = []
    for item in json_data:
        try:
            nome = item.get("nome", "").strip() or item.get("description", "").strip()
            if not nome:
                continue
                
            kcal = extract_nutrient_value(item.get("kcal", item.get("energy_kcal", 0)))
            prot = extract_nutrient_value(item.get("proteina_g", item.get("protein_g", 0)))
            lip = extract_nutrient_value(item.get("lipidios_g", item.get("lipid_g", 0)))
            carb = extract_nutrient_value(item.get("carboidratos_g", item.get("carbohydrate_g", 0)))
            
            alimento = AlimentoSQLiteBulk(
                nome=nome,
                kcal=kcal,
                proteina_g=prot,
                lipidios_g=lip,
                carboidratos_g=carb
            )
            alimentos.append(alimento)
        except Exception as e:
            logger.warning(f"Erro ao parsear alimento: {e}")
            continue
            
    return alimentos

def bulk_insert_sqlite(alimentos: list[AlimentoSQLiteBulk]):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Prepara a lista de tuplas ultra rápida baseada estritamente na DataClass iterável
    rows = [astuple(a) for a in alimentos]
    
    logger.info(f"Preparando Bulk Insert (Lightning Fast \u26a1) de {len(rows)} itens...")
    
    try:
        cursor.executemany('''
            INSERT OR IGNORE INTO alimentos (nome, kcal, proteina_g, lipidios_g, carboidratos_g)
            VALUES (?, ?, ?, ?, ?)
        ''', rows)
        conn.commit()
        logger.info(f"Sucesso! Banco SQLite local [{config.DB_PATH.name}] populado em bloco instantaneamente.")
    except Exception as e:
        logger.error(f"Erro fatal ao executar Bulk Insert no SQLite: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

def main():
    try:
        data = load_taco_data_from_file()
        alimentos = transform_food_data(data)
        if alimentos:
            bulk_insert_sqlite(alimentos)
        else:
            logger.warning("Nenhum dado processado do JSON.")
    except Exception as e:
        logger.error(f"Erro no pipeline principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
