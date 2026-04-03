import sys
from pathlib import Path

# Adiciona o diretório atual ao path para poder importar o pacote
sys.path.append(str(Path(__file__).parent.resolve()))

from nutriciones.services.google.auth_service import get_service_account_creds

def test_load_env():
    print("Iniciando teste de carregamento do .env...")
    try:
        # A função get_service_account_creds utiliza a config que carrega do dotenv logic
        creds = get_service_account_creds()
        
        print("\n[SUCESSO] Credenciais carregadas corretamente do config/.env!")
        print(f"Tipo do objeto retornado: {type(creds)}")
        print(f"Service Account Email carregado: {creds._service_account_email}")
        
    except ValueError as ve:
        print(f"\n[ERRO DE VALIDAÇÃO] Variáveis ausentes: {ve}")
        print("Verifique se as credenciais estão definidos corretamente no seu arquivo .env.")
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}")

if __name__ == "__main__":
    test_load_env()
