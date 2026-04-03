import sys
import uuid
import json
import logging
from dataclasses import dataclass, astuple
from pathlib import Path

# Adiciona o diretório principal ao sys.path para conseguirmos importar o modulo `nutriciones`
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from nutriciones.services.google.auth_service import get_ssot_sheets_service
from nutriciones.core import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Alimento:
    id_alimento: str
    nome: str
    grupo: str
    kcal: float
    proteina: float
    lipidios: float
    carboidratos: float

def extract_nutrient_value(val) -> float:
    """Extrai valor numérico tratado, lidando com 'NA', '*' ou Nulos e strings vazias."""
    if val is None or val == 'NA' or val == '*' or val == '':
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def transform_food_data(json_data: list) -> list[list]:
    """Converte a lista de dicionários locais em linhas estruturadas para o Sheets."""
    rows = []
    for item in json_data:
        try:
            nome = item.get("description", "Sem Nome")
            
            grupo = item.get("category", "Sem Grupo")
            if not isinstance(grupo, str) or not grupo:
                grupo = "Sem Grupo"
            
            kcal = extract_nutrient_value(item.get("energy_kcal"))
            proteina = extract_nutrient_value(item.get("protein_g"))
            lipidios = extract_nutrient_value(item.get("lipid_g"))
            carboidratos = extract_nutrient_value(item.get("carbohydrate_g"))
            
            alimento = Alimento(
                id_alimento=str(uuid.uuid4()),
                nome=nome,
                grupo=grupo,
                kcal=kcal,
                proteina=proteina,
                lipidios=lipidios,
                carboidratos=carboidratos
            )
            rows.append(list(astuple(alimento)))
        except Exception as e:
            logger.warning(f"Erro ao parsear alimento ID {item.get('id')}: {e}")
            continue
            
    return rows

def load_taco_data_from_file() -> list:
    """Lê o arquivo JSON local contendo os dados da TACO."""
    logger.info(f"Carregando dados locais do arquivo: {config.TACO_JSON_PATH}")
    
    with open(config.TACO_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def export_to_sheets(rows: list[list]):
    """Envia o bulk das linhas transacionadas para a planilha, incluindo cabeçalhos."""
    service = get_ssot_sheets_service()
    
    headers = [
        "id_alimento", 
        "nome", 
        "grupo", 
        "kcal", 
        "proteina_g", 
        "lipidios_g", 
        "carboidratos_g"
    ]
    
    final_rows = [headers] + rows
    body = {"values": final_rows}
    
    logger.info("Limpando dados antigos da aba db_alimentos!A:G...")
    service.spreadsheets().values().clear(
        spreadsheetId=config.GOOGLE_SHEET_ID_CARDAPIO,
        range="db_alimentos!A:G"
    ).execute()
    
    logger.info(f"Exportando {len(final_rows)} linhas (incluindo cabeçalho) para o Sheets...")
    result = service.spreadsheets().values().update(
        spreadsheetId=config.GOOGLE_SHEET_ID_CARDAPIO,
        range="db_alimentos!A1",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    logger.info(f"Exportação finalizada. Células atualizadas: {result.get('updatedCells')}")

def main():
    try:
        data = load_taco_data_from_file()
        rows = transform_food_data(data)
        if rows:
            export_to_sheets(rows)
        else:
            logger.warning("Nenhum dado processado.")
    except Exception as e:
        logger.error(f"Erro no pipeline de importação: {e}")

if __name__ == "__main__":
    main()
