import sys
import os

def check_venv():
    """Verifica se o script está rodando em um ambiente virtual."""
    # Heurística comum: se real_prefix ou base_prefix forem diferentes de sys.prefix
    is_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    if not is_venv:
        print("[X] ALERTA: Você não parece estar em um ambiente virtual (venv).")
        print("    Por favor, execute 'python setup_dev.py' e ative o ambiente '.venv' antes de prosseguir.")
        sys.exit(1)

if __name__ == "__main__":
    check_venv()
    print("=== NUTRICIONES SABLA (NSS) ===")
    print("[*] Ambiente isolado verificado.")
    # Aqui entraria a chamada pro seu ponto de entrada principal (API ou Task Runner)
    print("[✔] Sistema pronto para execução via Task Runner ou Interface.")
