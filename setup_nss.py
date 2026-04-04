import os
import sys
import subprocess
import venv
from pathlib import Path

# Configurações do Projeto NSS Sabla
PROJECT_ROOT = Path(__file__).parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
ENV_FILE = PROJECT_ROOT / ".env"
MIN_PYTHON_VERSION = (3, 10)

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    print(f"[*] Verificando versão do Python... (Atual: {sys.version_info.major}.{sys.version_info.minor})")
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"[X] Erro: O NutricioneS Sabla requer Python >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
        sys.exit(1)

def create_venv():
    """Cria o ambiente virtual isolado."""
    if not VENV_DIR.exists():
        print(f"[*] Criando ambiente virtual em {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)
        print("[✔] Ambiente virtual criado.")
    else:
        print("[*] Ambiente virtual já detectado.")

def get_pip_path():
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def install_dependencies():
    """Instala as dependências pinadas (Twelve-Factor Fator II)."""
    pip_path = get_pip_path()
    if not REQUIREMENTS_FILE.exists():
        print(f"[X] Erro: Arquivo {REQUIREMENTS_FILE} não encontrado.")
        sys.exit(1)
        
    print(f"[*] Instalando dependências críticas de {REQUIREMENTS_FILE.name}...")
    try:
        subprocess.check_call([str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)])
        print("[✔] Dependências instaladas com sucesso.")
    except Exception as e:
        print(f"[X] Falha na instalação: {e}")
        sys.exit(1)

def validate_env_keys():
    """Verifica se as chaves mínimas do .env estão presentes."""
    if not ENV_FILE.exists():
        print("[!] AVISO: Arquivo .env não encontrado. Crie um baseado no template.")
        return
    
    with open(ENV_FILE, "r") as f:
        content = f.read()
        needed_keys = ["GOOGLE_SHEET_ID_CARDAPIO", "GOOGLE_DOC_TEMPLATE_ID", "REDIS_URL"]
        for key in needed_keys:
            if key not in content:
                print(f"[!] AVISO: A chave {key} está ausente no seu .env.")
    
    print("\n[TIP] Para desenvolvimento local, você pode subir o Redis via Docker:")
    print("      docker run -d --name nss-redis -p 6379:6379 redis")

def create_folders():
    for folder in ["data", "logs"]:
        (PROJECT_ROOT / folder).mkdir(exist_ok=True)
    print("[✔] Pastas de sistema (data/, logs/) criadas.")

def main():
    print("==================================================")
    print("   NUTRICIONES SABLA - SETUP DE INFRAESTRUTURA   ")
    print("==================================================")
    
    check_python_version()
    create_folders()
    create_venv()
    install_dependencies()
    validate_env_keys()
    
    print("\n[🚀] O NutricioneS Sabla está pronto para agir!")
    print(f"Para ativar o ambiente: .\\.venv\\Scripts\\Activate.ps1 (Windows)")
    print(f"Para iniciar o fluxo diário: python scripts/executar_tarefas_diarias.py")
    print("==================================================")

if __name__ == "__main__":
    main()
