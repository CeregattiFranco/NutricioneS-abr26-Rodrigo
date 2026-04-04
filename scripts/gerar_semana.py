import sys
import os
import json
import uuid
import re
import logging
from pathlib import Path

# Configuração de PATH para acesso local
sys.path.insert(0, str(Path(__file__).parent.parent))

from crewai import Task, Crew
from nutriciones.agents.nutricionista_agent import criar_agente_nutricionista
from nutriciones.models.planos import PlanoAlimentar
from nutriciones.models.pacientes import Paciente
from nutriciones.services.dieta_service import salvar_plano_alimentar
from nutriciones.services.google.docs_service import criar_plano_alimentar_semanal
from nutriciones.services.google.sheets.indices import get_indices

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_agent_output(texto: str) -> list[dict]:
    """Extrai e valida o bloco JSON impresso pelo CrewAI."""
    logger.info("Processando saída crua do LLM...")
    
    match = re.search(r'```json\s*(.*?)\s*```', texto, re.DOTALL | re.IGNORECASE)
    bloco = match.group(1) if match else texto
    
    try:
        dados = json.loads(bloco)
        if type(dados) is dict and "planos" in dados:
            return dados["planos"]
        return dados if type(dados) is list else [dados]
    except json.JSONDecodeError as e:
        logger.error(f"Erro fatal ao decodificar JSON do agente: {e}")
        logger.debug(f"Conteúdo que falhou: {bloco}")
        raise ValueError("A IA não retornou um JSON válido.")

def main():
    pct_id = "paciente-teste-123"
    meta_kcal = 1800
    
    agente = criar_agente_nutricionista()
    
    tarefa = Task(
        description=(
            f"Você deve gerar OBRIGATORIAMENTE um cardápio de 7 dias (Segunda a Domingo) para o paciente '{pct_id}'. "
            f"A meta é {meta_kcal} kcal diárias (20% Café, 40% Almoço, 40% Jantar). "
            f"Utilize a tool 'Pesquisar Alimentos SSoT' para pesquisar 1 item por vez e 'Calcular Macronutrientes da Refeicao'. "
            f"Retorne o resultado final EXCLUSIVAMENTE em um formato de code block Markdown JSON, e certifique-se de fechar os colchetes."
        ),
        expected_output='''
Retorne APENAS um Markdown de ```json e ``` contendo o array exato de 7 dias com as chaves:
[
  {
    "dia": "Segunda-feira",
    "total_kcal": 1800.0,
    "total_proteina": 75.0,
    "total_carboidrato": 200.0,
    "total_lipidios": 40.0,
    "itens_detalhados": [
      {"nome": "Arroz, branco, cozido", "peso_g": 150.0, "kcal": 195.0},
      {"nome": "Feijão, carioca, cozido", "peso_g": 100.0, "kcal": 114.0}
    ]
  }
]
        ''',
        agent=agente
    )
    
    equipe = Crew(
        agents=[agente],
        tasks=[tarefa],
        verbose=True
    )
    
    logger.info("Iniciando a mente do CrewAI. Isso consultará o SQLite iterativamente (pode demorar alguns minutos)...")
    resultado = equipe.kickoff()
    texto_resultado = getattr(resultado, 'raw', str(resultado))
    
    dados_semana = parse_agent_output(texto_resultado)
    
    if len(dados_semana) < 7:
        logger.warning(f"O Agent retornou apenas {len(dados_semana)} dias. Prosseguindo mesmo assim.")
        
    objetos_planos = []
    lista_pdf = []
    
    total_kcal_semana = total_prot_semana = total_carb_semana = total_lip_semana = 0.0
    
    logger.info("Mapeando a resposta de IA para a Arquitetura Orientada e Docs de Apresentação...")
    for dia_json in dados_semana:
        # Preenchimento do DataModel para o SQLite/Sheets (SSoT do back-end)
        plano = PlanoAlimentar(
            plano_id=uuid.uuid4().hex,
            pct_id=pct_id,
            data=dia_json.get("dia", "Indefinido"),  # usamos dia da semana momentaneamente na coluna data
            total_kcal=float(dia_json.get("total_kcal", 0)),
            total_proteina=float(dia_json.get("total_proteina", 0)),
            total_carboidrato=float(dia_json.get("total_carboidrato", 0)),
            total_lipidios=float(dia_json.get("total_lipidios", 0)),
            itens_detalhados=json.dumps(dia_json.get("itens_detalhados", []), ensure_ascii=False)
        )
        objetos_planos.append(plano)
        
        # Consolidação Numérica de Médias
        total_kcal_semana += plano.total_kcal
        total_prot_semana += plano.total_proteina
        total_carb_semana += plano.total_carboidrato
        total_lip_semana += plano.total_lipidios
        
        # Preenchimento Formato Livre para o PDF Templates (conforme docs_service.py requer)
        lista_pdf.append({
            "dia": plano.data,
            "totais": {
                "kcal": plano.total_kcal,
                "proteina_g": plano.total_proteina,
                "carboidratos_g": plano.total_carboidrato,
                "lipidios_g": plano.total_lipidios
            },
            "itens_detalhados": dia_json.get("itens_detalhados", [])
        })

    logger.info("Persistindo matrizes no Sheets com atualização paralela O(1) Binária...")
    salvar_plano_alimentar(objetos_planos)
    
    logger.info("Auditando o arquivo Indices (O(1)) do Sheets gerado localmente...")
    indices = get_indices()
    b_refs = indices.get_back_references(
        foreign_sheet=Paciente,
        foreign_key=pct_id,
        primary_sheet=PlanoAlimentar
    )
    logger.info(f"O plano possui {len(b_refs)} chunks salvos nos Indices atualmente para o paciente.")
    
    logger.info("Formatando e Enviando Lotes de PDF para Google Docs...")
    # Resumo Semanal pro PDF
    dias = max(1, len(objetos_planos))
    resumo_pdf = {
        "kcal_media": round(total_kcal_semana / dias, 1),
        "proteina_media": round(total_prot_semana / dias, 1),
        "carboidrato_media": round(total_carb_semana / dias, 1),
        "lipidios_media": round(total_lip_semana / dias, 1),
    }
    
    pdf_id = criar_plano_alimentar_semanal(
        pct_id=pct_id, 
        resumo_semana=resumo_pdf, 
        planos_diarios=lista_pdf,
        nome_paciente="Paciente",
        sobrenome_paciente="Teste"
    )
    logger.info(f"✔ Script concluído com louvor! ID do PDF final no Drive: {pdf_id}")


if __name__ == "__main__":
    main()
