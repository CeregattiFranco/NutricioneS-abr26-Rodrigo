import sys
import uuid
import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# Ajuste no sys path para chamadas pela raiz
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from nutriciones.services.dieta_service import calcular_refeicao, salvar_plano_alimentar
from nutriciones.models.planos import PlanoAlimentar, ItemRefeicaoInput

def simular():
    meu_prato = [
        ItemRefeicaoInput(nome="Arroz, integral, cozido", peso_g=150.0),
        ItemRefeicaoInput(nome="Feijão, carioca, cozido", peso_g=100.0),
        ItemRefeicaoInput(nome="Batata Asterix Frita de Fast Food", peso_g=120.0) # Deve printar aviso de não encontrado e abortar computo deste index
    ]
    
    print("\n[MOTOR] Calculando macronutrientes da refeição base...\n")
    resultado = calcular_refeicao(meu_prato)
    
    print("\n=== RESUMO DO PARCIAL POR ITEM ===")
    for item in resultado.itens_analisados:
        print(f" -> {item.nome} ({item.peso_g}g)")
        print(f"    Kcal: {item.kcal:.2f} | Prot: {item.proteina_g:.2f}g | Lip: {item.lipidios_g:.2f}g | Carb: {item.carboidratos_g:.2f}g")
        
    if resultado.nao_encontrados:
        print("\n=== ERRO: ITENS NÃO ENCONTRADOS NO DB ===")
        for missed in resultado.nao_encontrados:
            print(f" -> [X] {missed}")
            
    print("\n==============================")
    print("      TOTAIS DA REFEIÇÃO      ")
    print("==============================")
    print(f" Calorias:     {resultado.kcal:.2f} kcal")
    print(f" Proteínas:    {resultado.proteina_g:.2f} g")
    print(f" Lipídios:     {resultado.lipidios_g:.2f} g")
    print(f" Carboidratos: {resultado.carboidratos_g:.2f} g")
    print("==============================\n")

    print("\n--- INICIANDO ROTINA DE SALVAMENTO AUTOMÁTICO (MOCK SIMULADO) ---")
    
    novo_plano = PlanoAlimentar(
        plano_id=str(uuid.uuid4()),
        cns_id="CNS-SIM-994", # ID mock da consulta
        data=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_kcal=resultado.kcal,
        total_proteina=resultado.proteina_g,
        total_carboidrato=resultado.carboidratos_g,
        total_lipidios=resultado.lipidios_g,
        itens_detalhados=json.dumps([asdict(it) for it in resultado.itens_analisados], ensure_ascii=False)
    )
    
    print(f"-> Serializando Plano para a Consulta {novo_plano.cns_id}...")
    try:
        salvar_plano_alimentar([novo_plano])
        print("\n[SUCESSO] Sincronização SSoT concluída na aba db_planosAlimentares!")
    except Exception as e:
        print(f"\n[FALHA] {e}")

if __name__ == "__main__":
    simular()

