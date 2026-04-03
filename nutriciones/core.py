import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_env_or_raise(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória não encontrada: {key}")
    return value

class Config:
    GOOGLE_SERVICE_ACCOUNT_EMAIL = get_env_or_raise("GOOGLE_SERVICE_ACCOUNT_EMAIL")
    GOOGLE_PRIVATE_KEY = get_env_or_raise("GOOGLE_PRIVATE_KEY")
    GOOGLE_PROJECT_ID = get_env_or_raise("GOOGLE_PROJECT_ID")
    GOOGLE_SHEET_ID_CARDAPIO = get_env_or_raise("GOOGLE_SHEET_ID_CARDAPIO")
    # GOOGLE_DOC_TEMPLATE_ID pode ser carregado se existir, senão pode falhar apenas onde for usado ou tentar carregar caso a string n esteja vazia
    GOOGLE_DOC_TEMPLATE_ID = os.getenv("GOOGLE_DOC_TEMPLATE_ID", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "taco.sqlite"
    TACO_JSON_PATH = DATA_DIR / "taco.json"

config = Config()
