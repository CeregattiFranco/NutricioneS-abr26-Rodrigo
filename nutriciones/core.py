import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    environment = os.getenv("NUTRICIONES_ENV", "dev")

    class Google:
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    class GoogleServices:
        sheet_id_cardapio = os.environ.get("GOOGLE_SHEET_ID_CARDAPIO", "")
        doc_template_id = os.environ.get("GOOGLE_DOC_TEMPLATE_ID", "")
        calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "")
        nutriciones_folder_id = os.environ.get("GOOGLE_DRIVE_FILE_ID", "")
        exams_sheet_template_id = os.environ.get("GOOGLE_EXAMS_SHEET_TEMPLATE_ID", "")

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "taco.sqlite"
    TACO_JSON_PATH = DATA_DIR / "taco.json"

config = Config()
