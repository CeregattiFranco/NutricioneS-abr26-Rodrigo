import os
import sys

# Adiciona o diretório atual ao path para poder importar o pacote
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nutriciones.services.google.auth_service import get_service_account_creds

def test_load_env():
    print("Iniciando teste de carregamento do .env...")
    try:
        # A função get_service_account_creds por padrão já chama load_dotenv() e
        # faz o tratamento do GOOGLE_PRIVATE_KEY substituindo \\n por \n.
        creds = get_service_account_creds()
        
        print("\n[SUCESSO] Credenciais carregadas corretamente do .env!")
        print(f"Tipo do objeto retornado: {type(creds)}")
        print(f"Service Account Email carregado: {creds._service_account_email}")
        
    except ValueError as ve:
        print(f"\n[ERRO DE VALIDAÇÃO] Variáveis ausentes: {ve}")
        print("Verifique se GOOGLE_SERVICE_ACCOUNT_EMAIL e GOOGLE_PRIVATE_KEY estão definidos corretamente no seu arquivo .env.")
    except ValueError as format_err:
        print(f"\n[ERRO DE FORMATO] Problema na estrutura da chave: {format_err}")
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}")

if __name__ == "__main__":
    test_load_env()
