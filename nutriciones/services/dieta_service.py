import os
import uuid
import json
import logging
from datetime import datetime
from dataclasses import dataclass, astuple
from dotenv import load_dotenv

from nutriciones.services.google.auth_service import get_ssot_sheets_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nova Estrutura para os Planos de Pacientes
@dataclass
class PlanoAlimentar:
    plano_id: str
    cns_id: str
    data: str
    total_kcal: float
    total_proteina: float
    total_carboidrato: float
    total_lipidios: float
    itens_detalhados: str # Formatado em texto/JSON

def fetch_alimentos_from_sheet() -> list[dict]:
    """Busca a aba db_alimentos atualizada e parseia como dicionários da tabela."""
    load_dotenv()
    sheet_id = os.getenv("GOOGLE_SHEET_ID_CARDAPIO")
    if not sheet_id:
        raise ValueError("Variável GOOGLE_SHEET_ID_CARDAPIO não encontrada no .env")
        
    service = get_ssot_sheets_service()
    
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="db_alimentos!A:G"
    ).execute()
    
    rows = result.get('values', [])
    if not rows:
        return []
        
    headers = rows[0]
    alimentos = []
    
    for row in rows[1:]:
        row_dict = {}
        for idx, header in enumerate(headers):
            row_dict[header] = row[idx] if idx < len(row) else 0.0
        alimentos.append(row_dict)
        
    return alimentos

def parse_float_br(val) -> float:
    """Tenta converter para float se precausando de pontuação locale brasileira nas planilhas."""
    if not val:
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def calcular_refeicao(itens_refeicao: list[dict]) -> dict:
    """
    Recebe itens_refeicao = [{"nome": str, "peso_g": float}, ...]
    As grandezas do banco SSoT referem-se a porções fixas de 100g.
    Para achar os macros: (Nutriente_da_TACO * peso_g) / 100.
    """
    logger.info("Sincronizando SSot com o DB Google Sheets...")
    db_alimentos = fetch_alimentos_from_sheet()
    
    # Cria o hash map para O(1) Time Complexity usando nome e normalizando lower case
    lookup_db = {item.get("nome", "").strip().lower(): item for item in db_alimentos}
    
    totais = {
        "kcal": 0.0,
        "proteina_g": 0.0,
        "lipidios_g": 0.0,
        "carboidratos_g": 0.0,
        "itens_analisados": [],
        "nao_encontrados": []
    }
    
    for request_item in itens_refeicao:
        nome = request_item.get("nome", "")
        nome_lower = nome.strip().lower()
        peso_g = float(request_item.get("peso_g", 0.0))
        
        db_ref = lookup_db.get(nome_lower)
        
        if not db_ref:
            logger.warning(f"Alimento '{nome}' não rastreado na base db_alimentos. Continuando cálculo sem ele...")
            totais["nao_encontrados"].append(nome)
            continue
            
        # Parse explícito dos campos
        kcal_100 = parse_float_br(db_ref.get("kcal", 0))
        prot_100 = parse_float_br(db_ref.get("proteina_g", 0))
        lip_100 = parse_float_br(db_ref.get("lipidios_g", 0))
        carb_100 = parse_float_br(db_ref.get("carboidratos_g", 0))
            
        fator_regra_de_tres = peso_g / 100.0
        
        # Consolida estrutura de resultado
        macro_item = {
            "nome": db_ref.get("nome"),
            "peso_g": peso_g,
            "kcal": round(kcal_100 * fator_regra_de_tres, 2),
            "proteina_g": round(prot_100 * fator_regra_de_tres, 2),
            "lipidios_g": round(lip_100 * fator_regra_de_tres, 2),
            "carboidratos_g": round(carb_100 * fator_regra_de_tres, 2),
        }
        
        # Soma global do prato
        totais["kcal"] += macro_item["kcal"]
        totais["proteina_g"] += macro_item["proteina_g"]
        totais["lipidios_g"] += macro_item["lipidios_g"]
        totais["carboidratos_g"] += macro_item["carboidratos_g"]
        
        totais["itens_analisados"].append(macro_item)
        
    # Arredondando os totais mestre para 2 casas decimais
    totais["kcal"] = round(totais["kcal"], 2)
    totais["proteina_g"] = round(totais["proteina_g"], 2)
    totais["lipidios_g"] = round(totais["lipidios_g"], 2)
    totais["carboidratos_g"] = round(totais["carboidratos_g"], 2)

    return totais

def salvar_plano_alimentar(planos: list[PlanoAlimentar]):
    """
    Usa o auth_service para assegurar os cabeçalhos em A1 e dar um append dos Planos Alimentares persistidos na aba db_planosAlimentares
    """
    if not planos:
        return
        
    load_dotenv()
    sheet_id = os.getenv("GOOGLE_SHEET_ID_CARDAPIO")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID_CARDAPIO não encontrado no .env")
        
    service = get_ssot_sheets_service()
    aba = "db_planosAlimentares"
    
    # 1. Garante de forma idempotente que os cabeçalhos estejam preenchidos na primeira linha
    headers = [
        "plano_id", "cns_id", "data", "total_kcal", 
        "total_proteina", "total_carboidrato", "total_lipidios", "itens_detalhados"
    ]
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{aba}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [headers]}
    ).execute()
    logger.info(f"Cabeçalhos garantidos e atualizados na aba {aba}!")
    
    # 2. Astuple mapeia o registro DataClass perfeitamente para uma list() ordenada e dá append
    rows_data = [list(astuple(plano)) for plano in planos]
    body = {
        "values": rows_data
    }
    
    logger.info(f"Executando Persistência na SSoT. Inserindo {len(planos)} dias de plano para Consulta: {planos[0].cns_id}...")
    
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{aba}!A:H",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        logger.info(f"Salvo com sucesso na aba {aba}! Updates: {result.get('updates', {}).get('updatedCells')} células alteradas.")
    except Exception as e:
        logger.error(f"Erro fatal ao executar Append do Plano Alimentar na aba {aba}: {e}")
        raise e
