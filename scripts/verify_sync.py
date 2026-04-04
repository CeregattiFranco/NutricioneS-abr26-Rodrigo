import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from nutriciones.services.google.sheets.base import get_ssot_sheets_service
from nutriciones.core import config

def check():
    service = get_ssot_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=config.GoogleServices.sheet_id_cardapio, 
        range='db_fathom!A:A'
    ).execute()
    values = result.get('values', [])
    print(f'TOTAL_REUNIOES: {len(values)}')

if __name__ == "__main__":
    check()
