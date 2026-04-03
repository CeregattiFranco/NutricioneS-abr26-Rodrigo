import os
import sys
import subprocess
import venv
from pathlib import Path

# Configurações do Projeto
PROJECT_ROOT = Path(__file__).parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
MIN_PYTHON_VERSION = (3, 10)

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    print(f"[*] Verificando versão do Python... (Atual: {sys.version_info.major}.{sys.version_info.minor})")
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"[X] Erro: Este projeto requer Python >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
        sys.exit(1)

def create_venv():
    """Cria o ambiente virtual se não existir."""
    if not VENV_DIR.exists():
        print(f"[*] Criando ambiente virtual em {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)
        print("[✔] Ambiente virtual criado.")
    else:
        print("[*] Ambiente virtual já existe.")

def get_pip_path():
    """Retorna o caminho do executável do pip dentro do venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def install_dependencies():
    """Instala as dependências via pip."""
    pip_path = get_pip_path()
    if not REQUIREMENTS_FILE.exists():
        print(f"[X] Erro: Arquivo {REQUIREMENTS_FILE} não encontrado.")
        sys.exit(1)
        
    print(f"[*] Instalando dependências de {REQUIREMENTS_FILE}...")
    try:
        subprocess.check_call([str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)])
        print("[✔] Dependências instaladas com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"[X] Erro ao instalar dependências: {e}")
        sys.exit(1)

def main():
    print("=== NSS SABLA: SETUP DO AMBIENTE DE DESENVOLVIMENTO ===")
    check_python_version()
    create_venv()
    install_dependencies()
    
    print("\n[✔] Setup concluído com sucesso!")
    print("\nPara ativar o ambiente virtual:")
    if sys.platform == "win32":
        print(f"    {VENV_DIR}\\Scripts\\Activate.ps1")
    else:
        print(f"    source {VENV_DIR}/bin/activate")
    print("\nExecute o projeto:")
    print("    python main.py")

if __name__ == "__main__":
    main()
