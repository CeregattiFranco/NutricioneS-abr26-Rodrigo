import json
from crewai import Agent
from crewai.tools import tool

from nutriciones.services.dieta_service import calcular_refeicao
from nutriciones.services.sqlite import pesquisar_alimento_nome
from nutriciones.models.planos import ItemRefeicaoInput

@tool("Pesquisar Alimentos SSoT")
def pesquisar_alimentos_ssot(termo: str) -> str:
    """Busque por APENAS UM ingrediente de cada vez para encontrar o NOME EXATO do alimento na base restrita TACO (SQLite) ANTES de calcular a refeição."""
    alimentos = pesquisar_alimento_nome(termo)
    resultados = [item.nome for item in alimentos]
    if not resultados:
        return f"Nenhum alimento encontrado com o termo '{termo}'. Tente nomes mais genéricos e unicos (ex: 'frango', 'arroz')."
    return f"Nomes Exatos encontrados na base: {', '.join(resultados[:15])}"

@tool("Calcular Macronutrientes da Refeicao")
def calcular_macronutrientes_tool(itens_json_str: str) -> str:
    """
    Recebe um array JSON rigoroso como string, no formato:
    [{"nome": "Nome Exato Encontrado na Pesquisa", "peso_g": 150.0}, {"nome": "NOME2", "peso_g": 85.0}]
    Retorna os macronutrientes totais da combinação.
    """
    try:
        itens_raw = json.loads(itens_json_str)
        itens = [ItemRefeicaoInput(**it) for it in itens_raw]
        resultado = calcular_refeicao(itens)
        
        return json.dumps({
            "kcal_total": resultado.kcal,
            "proteina_total": resultado.proteina_g,
            "lipidios_total": resultado.lipidios_g,
            "carboidrato_total": resultado.carboidratos_g,
            "analise_por_item": [f"{it.nome} ({it.peso_g}g): {it.kcal:.2f} kcal" for it in resultado.itens_analisados],
            "erros_nao_encontrados": resultado.nao_encontrados
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Erro ao processar as gramagens: {e}. Verifique o formato do JSON enviado (deve ser Array de Dicts)."

def criar_agente_nutricionista():
    return Agent(
        role="Nutricionista Especialista em Dietas Vegetarianas Estritas (Plant-Based)",
        goal="Montar cardápios diários 100% vegetarianos estritos, puramente à base de plantas, precisamente balanceados e criativos para os pacientes, não deixando a semana ser monótona.",
        backstory=(
            "Você é um nutricionista altamente metódico e muito criativo, focado em precisão matemática diária, "
            "que usa a base TACO SSoT como sua inquestionável fonte de verdade. "
            "Sua especialidade primária é o Vegetarianismo Estrito (Veganismo). **NUNCA PRESCREVA CARNES, FRANGO, PEIXE, OVOS, LEITE, QUEIJO, MEL OU PRODUTOS DE ORIGEM ANIMAL.** "
            "Você odeia cardápios super monótonos. Por isso você escuta o histórico dos dias passados da semana para propor leguminosas (feijões, lentilha, grão-de-bico), cereais, sementes, oleaginosas, hortaliças e frutas diferentes para seus pacientes. "
            "Você distribui precisamente o alimento focado num alvo: Café 20%, Almoço 40% e Jantar 40%. "
            "Você NUNCA adivinha. Você SEMPRE usa 'Pesquisar Alimentos SSoT' e logo após 'Calcular Macronutrientes da Refeicao'."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[pesquisar_alimentos_ssot, calcular_macronutrientes_tool]
    )
