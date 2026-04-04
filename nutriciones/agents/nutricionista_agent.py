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

from nutriciones.services.biometrics import extrair_historico_clinico, calcular_gap_objetivo, extrair_exames_recentes

@tool("Analisar Evolucao Paciente")
def analisar_evolucao_paciente(pct_id: str) -> str:
    """Consulte o histórico de evolução e EXAMES LABORATORIAIS para entender desfechos e deficiências ANTES de propor novas condutas."""
    try:
        historico = extrair_historico_clinico(pct_id)
        exames = extrair_exames_recentes(pct_id)
        
        analise = calcular_gap_objetivo(historico) if historico else "Sem histórico clínico."
        
        exm_fmt = "\n".join([f"  - {e['parametro']}: {e['valor']} {e['unidade']} ({e['status']})" for e in exames]) if exames else "Nenhum exame laboratoriais pendente."
        
        hist_recent = "\n".join([f"- {h['data']}: '{h['objetivo']}' -> '{h['conduta']}'" for h in historico[-2:]]) if historico else ""
        
        return (
            f"HISTÓRICO CLÍNICO:\n{hist_recent}\n\n"
            f"BIOMARCADORES (EXAMES):\n{exm_fmt}\n\n"
            f"CONCLUSÃO BIO-INTELLIGENCE:\n{analise}"
        )
    except Exception as e:
        return f"Erro ao analisar evolução: {e}"

def criar_agente_nutricionista():
    return Agent(
        role="Auditor e Nutricionista Bio-Intelligence (NSS Vision)",
        goal="Analisar desfechos históricos e BIOMARCADORES (Exames) para propor condutas nutricionais baseadas em evidências laboratoriais.",
        backstory=(
            "Você é um cientista de dados clínico. Antes de tudo, você usa 'Analisar Evolucao Paciente'. "
            "Se o paciente tiver um BIOMARCADOR em 'Alerta' (ex: Ferritina baixa), você DEVE ajustar a Conduta e o Diagnóstico imediatamente. "
            "Você é 100% Plant-Based e usa o TACO SSoT como guia. "
            "Se houver deficiência de ferro, você sugere leguminosas e vegetais verde-escuros. "
            "Você nunca ignora um exame alterado."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[pesquisar_alimentos_ssot, calcular_macronutrientes_tool, analisar_evolucao_paciente]
    )
