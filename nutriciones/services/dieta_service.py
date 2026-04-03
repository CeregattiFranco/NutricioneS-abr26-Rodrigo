import uuid
import json
import logging
from dataclasses import astuple

from nutriciones.core import config
from nutriciones.services.google.auth_service import get_ssot_sheets_service
from nutriciones.models.planos import PlanoAlimentar, ItemRefeicaoInput, MacroResult, TotaisRefeicao
from nutriciones.services.sqlite import get_alimento_exato

logger = logging.getLogger(__name__)

def calcular_refeicao(itens_refeicao: list[ItemRefeicaoInput]) -> TotaisRefeicao:
    """
    As grandezas referem-se a porções fixas de 100g.
    Para achar os macros: (Nutriente_da_TACO * peso_g) / 100.
    """
    totais = TotaisRefeicao(
        kcal=0.0,
        proteina_g=0.0,
        lipidios_g=0.0,
        carboidratos_g=0.0,
        itens_analisados=[],
        nao_encontrados=[]
    )
    
    for request_item in itens_refeicao:
        nome_lower = request_item.nome.strip().lower()
        peso_g = request_item.peso_g
        
        db_ref = get_alimento_exato(nome_lower)
        
        if not db_ref:
            logger.warning(f"Alimento '{request_item.nome}' não rastreado na base db_alimentos. Continuando cálculo sem ele...")
            totais.nao_encontrados.append(request_item.nome)
            continue
            
        kcal_100 = db_ref.kcal or 0.0
        prot_100 = db_ref.proteina_g or 0.0
        lip_100 = db_ref.lipidios_g or 0.0
        carb_100 = db_ref.carboidratos_g or 0.0
            
        fator_regra_de_tres = peso_g / 100.0
        
        macro_item = MacroResult(
            nome=db_ref.nome,
            peso_g=peso_g,
            kcal=kcal_100 * fator_regra_de_tres,
            proteina_g=prot_100 * fator_regra_de_tres,
            lipidios_g=lip_100 * fator_regra_de_tres,
            carboidratos_g=carb_100 * fator_regra_de_tres,
        )
        
        totais.kcal += macro_item.kcal
        totais.proteina_g += macro_item.proteina_g
        totais.lipidios_g += macro_item.lipidios_g
        totais.carboidratos_g += macro_item.carboidratos_g
        
        totais.itens_analisados.append(macro_item)
        
    return totais

from nutriciones.services.google.sheets.base import inserir_lista_recursos, inserir_recurso, sheet_name_of_resource_type
from nutriciones.services.google.sheets.types import PedidoInsercaoListaRecursos, PedidoInsercaoRecurso
from nutriciones.services.google.sheets.serializers.dieta import serialize_plano

def salvar_plano_alimentar(planos: list[PlanoAlimentar]):
    """
    Persiste os Planos Alimentares na SSoT e atualiza o cache de índices.
    """
    if not planos:
        return
        
    spreadsheet_name = sheet_name_of_resource_type[PlanoAlimentar]
    
    logger.info(f"Executando Persistência na SSoT. Inserindo {len(planos)} dias de plano para Consulta: {planos[0].pct_id}...")
    
    try:
        # Se desejar inserir um a um como o CTO exemplificou, usamos loop:
        # for plano in planos:
        #     inserir_recurso(PedidoInsercaoRecurso(
        #         spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        #         spreadsheet_name=spreadsheet_name,
        #         recurso=plano,
        #         serialize=serialize_plano
        #     ))
        
        # Inserção em batch (melhor performance):
        request = PedidoInsercaoListaRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name=spreadsheet_name,
            recursos=planos,
            serialize=serialize_plano
        )
        
        range_inserido = inserir_lista_recursos(request)
        logger.info(f"Salvo e indexado com sucesso na aba {spreadsheet_name}! Range: {range_inserido.raw}")
        
    except Exception as e:
        logger.error(f"Erro fatal ao executar Inserção do Plano Alimentar na aba {spreadsheet_name}: {e}")
        raise e
