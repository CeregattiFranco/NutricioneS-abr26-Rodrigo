import uuid
import logging
from datetime import datetime, date
from dataclasses import astuple
from typing import Sequence

from nutriciones.core import config
from nutriciones.models.pacientes import Paciente, PacienteEndereco, PacienteTelefone, PacienteEmail
from nutriciones.services.google.sheets.base import inserir_lista_recursos, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoInsercaoListaRecursos
from nutriciones.services.google.drive import find_patient_folder

logger = logging.getLogger(__name__)

def generic_serializer(recurso) -> Sequence[str]:
    def stringify(val):
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        if val is None:
            return ""
        if isinstance(val, (datetime, date)):
            # Formato compatível de data, dependendo da UI (Ex: YYYY-MM-DD HH:MM:SS)
            return val.isoformat()
        return str(val)

    return [stringify(v) for v in astuple(recurso)]

def embarcar_paciente(
    nome: str,
    sobrenome: str,
    cpf: str,
    data_nascimento: date,
    telefone: str,
    email: str,
    logradouro: str,
    numero: str,
    cep: str,
    bairro: str,
    cidade: str,
    uf: str
):
    """
    Cadastra um paciente e seus arrays atômicos de forma orquestrada, e ativa a infra de Drive.
    """
    logger.info(f"Iniciando embarque atômico para o paciente: {nome} {sobrenome}")
    
    pct_id = uuid.uuid4().hex
    agora = datetime.now()
    
    paciente = Paciente(
        pct_id=pct_id,
        nome=nome,
        sobrenome=sobrenome,
        cpf=cpf,
        data_nascimento=data_nascimento,
        responsavel_id="",
        status="ativo",
        origem="embarque",
        ativo=True,
        created_at=agora,
        updated_at=agora
    )
    
    telefone_obj = PacienteTelefone(
        tel_id=uuid.uuid4().hex,
        pct_id=pct_id,
        ddi="55",
        ddd=telefone[:2] if len(telefone) > 2 else "11",
        telefone=telefone[2:] if len(telefone) > 2 else telefone,
        whatsapp=True,
        contato_principal=True,
        ativo=True,
        created_at=agora,
        updated_at=agora
    )
    
    email_obj = PacienteEmail(
        mail_id=uuid.uuid4().hex,
        pct_id=pct_id,
        email=email,
        validado=False,
        opt_in_data=agora,
        email_principal=True,
        ativo=True,
        created_at=agora,
        updated_at=agora
    )
    
    endereco_obj = PacienteEndereco(
        adr_id=uuid.uuid4().hex,
        pct_id=pct_id,
        cep=cep,
        logradouro=logradouro,
        numero=numero,
        complemento="",
        bairro=bairro,
        cidade=cidade,
        uf=uf,
        pais="Brasil",
        endereco_nfse=True,
        ativo=True,
        created_at=agora,
        updated_at=agora
    )
    
    # Prepara inserção em lote para o motor base de sheets
    recursos_pacientes = [paciente]
    recursos_telefones = [telefone_obj]
    recursos_emails = [email_obj]
    recursos_enderecos = [endereco_obj]
    
    spreadsheet_id = config.GoogleServices.sheet_id_cardapio
    
    logger.info("Executando inserção primária na aba db_pacientes...")
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_name=sheet_name_of_resource_type[Paciente],
        recursos=recursos_pacientes,
        serialize=generic_serializer
    ))
    
    logger.info("Executando inserções relacionais (telefones, e-mails, endereços)...")
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_name=sheet_name_of_resource_type[PacienteTelefone],
        recursos=recursos_telefones,
        serialize=generic_serializer
    ))
    
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_name=sheet_name_of_resource_type[PacienteEmail],
        recursos=recursos_emails,
        serialize=generic_serializer
    ))
    
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_name=sheet_name_of_resource_type[PacienteEndereco],
        recursos=recursos_enderecos,
        serialize=generic_serializer
    ))
    
    logger.info("Configuração Google Sheets persistida! Iniciando provisionamento Google Drive...")
    
    try:
        # Padrão contextualizado: Encontra ou cria a pasta raiz do paciente
        find_patient_folder(pct_id, nome=nome, sobrenome=sobrenome)
    except Exception as e:
        logger.error(f"Erro ao provisionar pasta do paciente no Drive: {e}")

    logger.info(f"Embarque do paciente {pct_id} concluído com sucesso!")
    return pct_id
