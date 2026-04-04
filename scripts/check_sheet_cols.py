import os
import sys

# Garante que o diretório raiz está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nutriciones.core import config
from nutriciones.services.google import auth_service

def check_cols():
    service = auth_service.get_ssot_sheets_service()
    sheet_id = config.GoogleServices.sheet_id_cardapio
    res = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="db_fathom!A1:AZ1"
    ).execute()
    
    values = res.get("values", [])
    if not values:
        print("Planilha vazia")
        return
    
    header = values[0]
    print(f"Total de colunas: {len(header)}")
    for i, col in enumerate(header):
        print(f"{i+1}: {col}")

if __name__ == "__main__":
    check_cols()
