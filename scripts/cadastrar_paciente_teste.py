import sys
import logging
from pathlib import Path
from datetime import date

# Garante path absoluto
sys.path.insert(0, str(Path(__file__).parent.parent))

from nutriciones.services.pacientes import embarcar_paciente
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.models.pacientes import Paciente, PacienteEmail, PacienteTelefone, PacienteEndereco

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=== TESTE DE INTEGRAÇÃO: EMBARQUE ATÔMICO DE PACIENTE ===")
    
    # Executa o cadastro que fará inserções nos db_* e na nuvem do Drive
    novo_pct_id = embarcar_paciente(
        nome="Lucas",
        sobrenome="Andrade",
        cpf="12345678900",
        data_nascimento=date(1990, 5, 20),
        telefone="11987654321",
        email="lucas.andrade.teste@nutriciones.com",
        logradouro="Avenida Paulista",
        numero="1000",
        cep="01310-100",
        bairro="Bela Vista",
        cidade="São Paulo",
        uf="SP"
    )
    
    logger.info("\n=== VERIFICANDO RESULTADOS NOS ÍNDICES (MEMÓRIA O(1)) ===")
    
    try:
        # Recupera memória binária sem fazer network fetch
        indices = get_indices()
    except Exception as e:
        logger.error(f"Índices não puderam ser carregados: {e}")
        return
        
    range_paciente = indices.get_range_from_pk(Paciente, novo_pct_id)
    if not range_paciente:
        logger.error("Falha ao encontrar o paciente indexado na memória!")
        return
        
    logger.info(f"[✔] Paciente {novo_pct_id} alocado perfeitamente na Planilha no range '{range_paciente.raw}'")

    # Verificando relacionamento Has-Many do Endereço via Foreign Keys
    enderecos_ids = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key=novo_pct_id,
        primary_sheet=PacienteEndereco
    )
    logger.info(f"[✔] Endereços Indexados e Mapeados Corretamente: {len(enderecos_ids)}")

    telefones_ids = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key=novo_pct_id,
        primary_sheet=PacienteTelefone
    )
    logger.info(f"[✔] Telefones Indexados e Mapeados Corretamente: {len(telefones_ids)}")

    emails_ids = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key=novo_pct_id,
        primary_sheet=PacienteEmail
    )
    logger.info(f"[✔] E-mails Indexados e Mapeados Corretamente: {len(emails_ids)}")

if __name__ == "__main__":
    main()
