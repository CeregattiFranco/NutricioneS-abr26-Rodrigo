import sys
import logging
from pathlib import Path

# Setup Project Path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from nutriciones.services.search.firecrawler import FirecrawlExplorer

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=== NSS INTELLIGENCE: TESTANDO PESQUISA CLÍNICA (FIRECRAWL) ===")
    tema = "beneficios do Inositol na SOP"
    print(f"[*] Pesquisando evidência científica para: {tema}...")
    
    try:
        explorer = FirecrawlExplorer()
        resultado = explorer.pesquisar_evidencias(tema)
        
        print("\n=== RESULTADO DA PESQUISA CLÍNICA ===")
        print(resultado)
        print("=======================================")
        print("\n[✔] Teste de pesquisa concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"[X] Erro na pesquisa clínica: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
