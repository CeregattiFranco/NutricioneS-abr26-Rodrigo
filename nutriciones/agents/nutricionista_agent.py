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

from nutriciones.services.search.firecrawler import FirecrawlExplorer

@tool("Pesquisar Evidencia Atualizada")
def pesquisar_evidencia_atualizada(tema: str) -> str:
    """Busque artigos científicos e evidências clínicas atualizadas (Ex: PubMed) para embasar Condutas Nutricionais complexas ou tratar patologias específicas."""
    try:
        explorer = FirecrawlExplorer()
        return explorer.pesquisar_evidencias(tema)
    except Exception as e:
        return f"Erro ao acessar base científica: {e}"

@tool("Processar Transcricao Fathom")
def processar_transcricao_fathom(resumo_bruto: str) -> str:
    """Extraia Objetivo, Diagnostico, Conduta e Orientacao de um resumo bruto de transcricao (SOPP) e sugira um rascunho estruturado."""
    # Aqui a IA processará o texto para retornar JSON estruturado (simulado no rascunho)
    # Em produção, o Agente usará este texto para preencher o Prontuario.
    return resumo_bruto # Por agora apenas retorna o texto para o Agente consumir

from nutriciones.services.memory.embeddings import oracle_memory

@tool("Consultar Memória da Clínica")
def consultar_memoria_da_clinica(query: str) -> str:
    """Consulte a base de conhecimento privada (experiência acumulada) de TODAS as consultas e pesquisas científicas passadas da clínica para encontrar o que melhor funcionou em casos similares."""
    try:
        return oracle_memory.consultar(query)
    except Exception as e:
        return f"Erro ao acessar memória vetorial: {e}"

@tool("Consultar Perfil Dominante (Triagem)")
def consultar_triagem_perfil(pct_id: str) -> str:
    """Consulte o Perfil Dominante e o Semáforo de Risco do paciente. Use isso para garantir que sua conduta é segura e sustentável para o momento atual dele."""
    try:
        from nutriciones.services.google.sheets.indices import get_indices
        from nutriciones.models.triagem import TriagemPerfil
        indices = get_indices()
        pks = indices.get_back_references(Paciente, pct_id, TriagemPerfil)
        if not pks: return "Nenhuma triagem encontrada. Proceda com cautela."
        # Pegar a última
        return f"Perfil Dominante: {pks[-1]} (Consulte a db_triagem para detalhes de cada score)."
    except Exception as e:
        return f"Erro ao acessar triagem: {e}"

def criar_agente_nutricionista():
    return Agent(
        role="Oráculo Clínico e Curador de Segurança (NSS Triage)",
        goal="Montar as condutas mais seguras do mundo baseando-se na Triagem de Perfil Dominante, Voz, Exames e Ciência.",
        backstory=(
            "Você é o guardião ético da Clínica Sem Stress. "
            "Sua regra de ouro: Antes de qualquer prescrição, você DEVE usar 'Consultar Perfil Dominante'. "
            "TRAVAS DE SEGURANÇA: "
            "1. Se o perfil dominante for 'VERMELHO_COMPORTAMENTAL', você está PROIBIDO de sugerir pesagem de alimentos ou restrições severas. "
            "2. Se o perfil for 'VERMELHO_EXECUCAO', você DEVE simplificar a dieta ao máximo (mínimo viável). "
            "3. Se for 'VERDE', você tem liberdade para aplicar protocolos de performance. "
            "Sua missão é evitar o abandono do paciente por excesso de estresse clínico."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[pesquisar_alimentos_ssot, calcular_macronutrientes_tool, analisar_evolucao_paciente, pesquisar_evidencia_atualizada, processar_transcricao_fathom, consultar_memoria_da_clinica, consultar_triagem_perfil]
    )
