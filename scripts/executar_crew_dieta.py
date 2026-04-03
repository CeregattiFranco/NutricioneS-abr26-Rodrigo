import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.resolve()))

from crewai import Task, Crew, Process
from nutriciones.agents.nutricionista_agent import criar_agente_nutricionista
from nutriciones.core import config

def executar_plano_semanal():
    if not config.OPENAI_API_KEY:
        print("[AVISO]: Variável OPENAI_API_KEY ausente do seu .env. O CrewAI usará OpenAI default.")

    nutri_agent = criar_agente_nutricionista()
    
    if len(sys.argv) > 1:
        meta_diaria = float(sys.argv[1])
    else:
        meta_interativa = input("Digite a Meta Diária de Calorias do Paciente (ex: 1800): ")
        meta_diaria = float(meta_interativa) if meta_interativa.strip() else 1800.0

    dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    
    plano_7_dias = {}
    historico_fontes = ""
    
    print(f"\n[🚀 MOTOR CREW AI] Iniciando Orquestração do Plano de 7 Dias ({meta_diaria} kcal/dia)...")
    
    for dia in dias_da_semana: 
        print(f"\n--- Estruturando cardápio clínico para: {dia} ---")
        
        tarefa_dia = Task(
            description=(
                f"Gere o cardápio EXATO de {dia} para o paciente. \n"
                f"Meta Calórica Restrita: {meta_diaria} kcal totais ao fim do dia. \n"
                f"Regra de Fração: Café da Manhã (~20%), Almoço (~40%) e Jantar (~40%).\n"
                f"Regra Dietética Absoluta: A DIETA DEVE SER 100% VEGETARIANA ESTRITA (VEGANA). NUNCA INCLUA NENHUM PRODUTO DE ORIGEM ANIMAL.\n"
                f"Atenção à Variedade: NUNCA repita o mesmo prato ou a base proteica exata dos dias anteriores. Resumo dos dias anteriores gerados para você tentar NÃO repetir: {historico_fontes if historico_fontes else 'Nenhuma, este é o primeiro dia.'}\n\n"
                "Execução por Refeição:\n"
                "1. Pesquise nomes oficiais precisos (ex: feijão, grão-de-bico, lentilha, castanhas, tofu, aveia, batatas, arroz, brócolis) na SSoT com a ferramenta de busca.\n"
                "2. Jogue na ferramenta de cálculo validando gramagens para bater os 20% ou 40% das KCAL com fontes unicamente vegetais.\n"
                "3. Forme as 3 refeições sólidas.\n\n"
                f"Entregue APENAS o detalhamento formatado de {dia} com as 3 refeições limpas, listando seus alimentos pesados e a prova final das calorias totais batendo com a meta."
            ),
            expected_output=f"Relatório matador detalhando {dia} com 3 refeições, ingredientes 100% vegetarianos em gramas, calorias e macros totais calculados e balanceados da meta de {meta_diaria}kcal.",
            agent=nutri_agent
        )
        
        crew = Crew(
            agents=[nutri_agent],
            tasks=[tarefa_dia],
            verbose=False, 
            process=Process.sequential
        )
        
        # Roda a mágica no LLM para o dia específico em iterador
        resultado_dia = crew.kickoff()
        plano_7_dias[dia] = resultado_dia
        
        # Alimenta o histórico de memória do orquestrador
        historico_fontes += f" [{dia}: {resultado_dia.raw}] "
        
    print("\n\n" + "="*50)
    print("        RESULTADO FINAL DO PLANO SEMANAL")
    print("="*50)
    
    for dia, resultado in plano_7_dias.items():
        print(f"\n============== {dia.upper()} ==============")
        print(resultado)
        
    print("\n[INFO] Lógica Loop do CrewAI validada com sucesso! Pronto para anexar a persistência nas Sheets!")

if __name__ == "__main__":
    executar_plano_semanal()
