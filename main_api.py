import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
import uvicorn
import os
import uuid

from nutriciones.services.google.auth_service import get_auth_flow, save_token, get_creds
from nutriciones.core import config, get_base_logger, correlation_id_ctx, notify_critical_failure
from nutriciones.services.google.sheets.indices import refresh_indices, get_indices

logger = get_base_logger("NSS-API")

app = FastAPI(title="NutricioneS Sabla - API & Onboarding")

# Middleware para Correlation ID (Fator XI)
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
    token = correlation_id_ctx.set(corr_id)
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response
    finally:
        correlation_id_ctx.reset(token)

# Base URL para redirecionamento (Pode ser configurado no .env)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@app.get("/")
def home():
    logger.info("Acesso à Home da API.")
    return {"status": "online", "message": "NutricioneS Sabla API is running."}

@app.get("/onboarding/google")
def google_onboarding():
    """Inicia o fluxo de consentimento do Google."""
    logger.info("Iniciando redirecionamento para Google OAuth Consent.")
    flow = get_auth_flow(redirect_uri=f"{BASE_URL}/onboarding/google/callback")
    
    # PKCE: O Flow do Google gera um code_verifier automaticamente
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
    
    # Salvar o code_verifier no Redis vinculado ao state para recuperar no callback (Stateless - Fator VI)
    r = get_indices().redis_client
    if r:
        r.set(f"nss:auth:state:{state}", flow.code_verifier, ex=600) # Expira em 10 min
    
    return RedirectResponse(auth_url)

@app.get("/onboarding/google/callback")
def google_callback(request: Request, background_tasks: BackgroundTasks):
    """Recebe o callback do Google, troca pelo token e inicializa os índices."""
    logger.info("Callback do Google recebido. Processando código de autorização.")
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code:
        logger.error("Código de autorização ausente no callback.")
        return {"error": "Código de autorização não recebido."}
        
    flow = get_auth_flow(redirect_uri=f"{BASE_URL}/onboarding/google/callback")
    
    # Recuperar code_verifier do Redis para satisfazer o PKCE
    r = get_indices().redis_client
    if r and state:
        code_verifier = r.get(f"nss:auth:state:{state}")
        if code_verifier:
            # Em versões recentes, o Flow espera que você defina o verifier se for manual
            flow.code_verifier = code_verifier if isinstance(code_verifier, str) else code_verifier.decode()
    
    flow.fetch_token(code=code)
    
    creds = flow.credentials
    save_token(creds.to_json())
    
    # Disparar refresh de índices em background
    logger.info("Autenticação concluída. Disparando refresh de índices em background.")
    background_tasks.add_task(refresh_indices, acknowledge_costly_operation=True)
    
    return {
        "status": "success", 
        "message": "Autenticação Google concluída e persistida no Redis. Sincronização de dados iniciada em background."
    }

from nutriciones.services.biometrics import extrair_historico_clinico, calcular_gap_objetivo

import uuid
from typing import List, Dict
from pydantic import BaseModel

class ExameInput(BaseModel):
    parametro: str
    valor: float
    unidade: str
    ref_min: float
    ref_max: float
    pct_id: str

@app.post("/webhook/n8n/exames")
async def webhook_ocr_exames(exames: List[ExameInput], background_tasks: BackgroundTasks):
    """
    Ingestão estruturada de dados de OCR (Exames de Sangue).
    """
    logger.info(f"Recebido Webhook OCR com {len(exames)} parâmetros laboratoriais.")
    
    from nutriciones.models.biometria import ExameLaboratorial
    from nutriciones.services.google.sheets.base import inserir_lista_recursos, sheet_name_of_resource_type, PedidoInsercaoListaRecursos
    from nutriciones.services.pacientes import generic_serializer
    
    novos_exames = []
    for ex in exames:
        obj = ExameLaboratorial(
            exm_id=uuid.uuid4().hex[:10],
            pct_id=ex.pct_id,
            parametro=ex.parametro,
            valor=ex.valor,
            unidade=ex.unidade,
            referencia_min=ex.ref_min,
            referencia_max=ex.ref_max
        )
        novos_exames.append(obj)
        
        # Alerta para o Oracle se fora da ref
        if obj.valor < obj.referencia_min or obj.valor > obj.referencia_max:
             oracle_memory.adicionar_memoria(
                 texto=f"Deficiência/Excesso detectada: {obj.parametro} em {obj.valor} {obj.unidade}",
                 metadata={"tipo": "exame", "parametro": obj.parametro}
             )
        
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[ExameLaboratorial],
        recursos=novos_exames,
        serialize=generic_serializer
    ))
    
    # Atualizar indices no Redis (Background) para o Agente ler os novos dados
    background_tasks.add_task(refresh_indices, acknowledge_costly_operation=True)
    
    return {"status": "success", "ingested": len(novos_exames)}

from nutriciones.services.fathom_service import FathomClient

class FathomWebhookInput(BaseModel):
    call_id: str

@app.post("/webhook/fathom/call-ended")
async def webhook_fathom_call(data: FathomWebhookInput, background_tasks: BackgroundTasks):
    """
    Recebe evento de fim de chamada do Fathom e inicia processamento do prontuário.
    """
    logger.info(f"Fathom Webhook: Chamada finalizada detectada. ID: {data.call_id}")
    
    # Processamento em background pois envolve chamadas a APIs de IA e Google
    background_tasks.add_task(processar_rascunho_fathom, data.call_id)
    
    return {"status": "processing", "call_id": data.call_id}

async def processar_rascunho_fathom(call_id: str):
    """Orquestra a IA para ler a transcrição e gerar rascunho de prontuário."""
    correlation_id_ctx.set(f"FATHOM-{call_id[:8]}")
    try:
        fathom = FathomClient()
        detalhes = fathom.buscar_detalhes_chamada(call_id)
        resumo = detalhes.get("transcript_summary", "")
        
        # Aqui o agente entra em cena (Stub da chamada do agente)
        # O agente usaria processar_transcricao_fathom() tool internamente
        logger.info("IA processando resumo da consulta Fathom...")
        
        # Simulando sugestão estruturada da IA
        from nutriciones.models.rascunhos import RascunhoClinico
        from nutriciones.services.google.sheets.base import inserir_lista_recursos, sheet_name_of_resource_type, PedidoInsercaoListaRecursos
        from nutriciones.services.pacientes import generic_serializer
        from datetime import datetime
        
        rascunho = RascunhoClinico(
            ras_id=uuid.uuid4().hex[:10],
            cns_id="CNS_PENDING", # Seria correlacionado via agenda
            pct_id="PCT_PENDING", 
            objetivo_sugerido="Aumentar energia e sono",
            diagnostico_sugerido="Fadiga adrenal e baixa ingestão proteica",
            conduta_sugerida="Suplementar Magnésio e 30g proteína/jantar",
            orientacao_sugerida="Higiene do sono (sem telas 1h antes)",
            fonte="Fathom AI"
        )
        
        inserir_lista_recursos(PedidoInsercaoListaRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name=sheet_name_of_resource_type[RascunhoClinico],
            recursos=[rascunho],
            serialize=generic_serializer
        ))
        
        logger.info("Rascunho clínico gerado e salvo no SSoT com sucesso.")
        
        # Guardar na memória da clínica (NSS Oracle)
        oracle_memory.adicionar_memoria(
            texto=f"Consulta: {rascunho.objetivo_sugerido}. Conduta: {rascunho.conduta_sugerida}",
            metadata={"tipo": "consulta", "data": datetime.now().isoformat(), "pct_id": "PCT_PENDING"}
        )
        
        refresh_indices(acknowledge_costly_operation=True)
        
    except Exception as e:
        logger.error(f"Erro ao processar rascunho Fathom: {e}")
        notify_critical_failure(f"Falha na ingestão Fathom ID {call_id}: {e}")

import hmac
import hashlib
from fastapi import Header, HTTPException

def verify_fathom_signature(payload: bytes, signature: str) -> bool:
    """Valida a assinatura HMAC-SHA256 do Fathom (Segurança NSS Listen)."""
    if not config.FATHOM_WEBHOOK_SECRET:
        logger.warning("FATHOM_WEBHOOK_SECRET não configurado. Ignorando validação (Cuidado!).")
        return True
    
    expected_signature = hmac.new(
        config.FATHOM_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@app.post("/webhook/fathom")
async def secure_fathom_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_fathom_signature: str = Header(None)
):
    """
    Endpoint Seguro para recepção de eventos Fathom (Sincronização em tempo real).
    """
    payload = await request.body()
    
    if not verify_fathom_signature(payload, x_fathom_signature):
        logger.error("Falha na validação da assinatura X-Fathom-Signature. Requisição rejeitada.")
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    call_id = data.get("call_id")
    
    if not call_id:
        return {"status": "error", "message": "call_id missing"}

    correlation_id_ctx.set(f"FTH-WEB-{call_id[:6]}")
    logger.info(f"[INFO] [NSS-FATHOM] - Webhook Fathom recebido para chamada: {call_id}")

    # Idempotência (Fator VI)
    from nutriciones.services.google.sheets.indices import get_indices
    r = get_indices().redis_client
    if r and r.exists(f"nss:fathom:received:{call_id}"):
        logger.info(f"[INFO] [NSS-FATHOM] - Chamada {call_id} já está sendo processada.")
        return {"status": "already_received", "call_id": call_id}

    # Marcar no Redis antes de disparar background
    if r:
        r.set(f"nss:fathom:received:{call_id}", "received", ex=3600)

    # Disparar pipeline de processamento em background
    background_tasks.add_task(processar_rascunho_fathom, call_id)
    
    return {"status": "accepted", "call_id": call_id}

from nutriciones.services.memory.embeddings import oracle_memory

from nutriciones.services.triagem_service import processar_respostas_triage

class TriagemInput(BaseModel):
    pct_id: str
    respostas: Dict[str, int]
    nss_forms_token: str

@app.post("/webhook/forms/triagem")
async def webhook_forms_triagem(data: TriagemInput, background_tasks: BackgroundTasks):
    """
    Ingestão de Perfil Dominante via Google Forms (NSS Triage).
    """
    # Validação de Segurança
    token_esperado = os.getenv("NSS_FORMS_TOKEN", "nss_secret_123")
    if data.nss_forms_token != token_esperado:
        logger.warning(f"Tentativa de triagem com token inválido para pct_id: {data.pct_id}")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid NSS Forms Token")

    correlation_id_ctx.set(f"TRI-{data.pct_id[:6]}")
    logger.info(f"[INFO] [NSS-TRIAGE] - Triagem recebida para paciente: {data.pct_id}")
    
    # Processamento em background para resposta rápida ao Webhook
    background_tasks.add_task(processar_persistência_triagem, data)
    
    return {"status": "accepted", "pct_id": data.pct_id}

async def processar_persistência_triagem(data: TriagemInput):
    """Pipeline de Persistência e Auditoria da Triagem."""
    try:
        resultado = processar_respostas_triage(data.pct_id, data.respostas)
        
        from nutriciones.services.google.sheets.base import inserir_lista_recursos, PedidoInsercaoListaRecursos, sheet_name_of_resource_type
        from nutriciones.models.triagem import TriagemPerfil
        
        inserir_lista_recursos(PedidoInsercaoListaRecursos(
            spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
            spreadsheet_name=sheet_name_of_resource_type[TriagemPerfil],
            spreadsheet_range="A2:Z",
            recursos=[resultado],
            serialize=lambda r: [
                r.tri_id, r.pct_id, 
                r.score_metabolico, r.score_comportamental, 
                r.score_execucao, r.score_expectativa, 
                r.score_seguranca, r.dominante_sugerido, 
                r.data_triagem.isoformat()
            ]
        ))
        
        logger.info(f"[INFO] [NSS-TRIAGE] - Perfil Dominante salvo no SSoT: {resultado.dominante_sugerido}")
        
        refresh_indices(acknowledge_costly_operation=True)
        
    except Exception as e:
        logger.error(f"Erro ao processar triagem: {e}")

from nutriciones.services.analytics import nss_analytics

@app.get("/clinica/analytics")
def get_clinic_performance():
    """
    NSS Analytics: Dashboard de Performance Clínica e Governança de Resultados.
    """
    logger.info("[INFO] [NSS-ANALYTICS] - Consulta de auditoria de performance recebida.")
    try:
        dados = nss_analytics.calcular_performance_clinica()
        return {
            "status": "active",
            "stats": dados,
            "correlation_id": correlation_id_ctx.get()
        }
    except Exception as e:
        logger.error(f"Erro no Analytics Auditor: {e}")
        return {"error": str(e)}

@app.get("/oracle/query")
def oracle_clinical_query(q: str):
    """
    NSS Oracle: Consulta a base de conhecimento privada da clínica via busca semântica.
    """
    logger.info(f"[INFO] [NSS-ORACLE] - Consulta semântica recebida: {q}")
    try:
        resultado = oracle_memory.consultar(q)
        return {
            "query": q,
            "analise_oracle": resultado,
            "correlation_id": correlation_id_ctx.get()
        }
    except Exception as e:
        logger.error(f"Erro no Oracle Query: {e}")
        return {"error": str(e)}

class ChatInput(BaseModel):
    text: str
    session_id: str = "default"

@app.post("/chat/command")
async def clinical_chat_command(data: ChatInput):
    """
    NSS Command: Centro de Comando Agêntico via Linguagem Natural.
    """
    correlation_id_ctx.set(f"CHAT-{data.session_id[:6]}")
    logger.info(f"[INFO] [NSS-COMMAND] - Recebido comando: {data.text}")
    
    from nutriciones.agents.nutricionista_agent import criar_agente_nutricionista
    from nutriciones.services.google.sheets.indices import get_indices
    
    indices = get_indices()
    r = indices.redis_client
    
    # 1. Recuperar contexto da sessão (Fator VI)
    contexto = ""
    if r:
        contexto = r.get(f"nss:chat:session:{data.session_id}") or ""
    
    # 2. Orquestração Agêntica
    agent = criar_agente_nutricionista()
    
    # Prompt de Orquestração (Roteamento de Intenções)
    full_query = f"""
    Contexto da Conversa Atual: {contexto}
    
    Comando do Profissional: {data.text}
    
    Sua missão é responder de forma curta e clínica. Use suas ferramentas para:
    - Buscar dados do paciente (SSoT)
    - Consultar exames (Vision)
    - Consultar a memória da clínica (Oracle)
    - Pesquisar no PubMed (Intelligence)
    
    Se o profissional pedir para preparar um rascunho, use os dados coletados.
    """
    
    try:
        # Nota: Em um ambiente CrewAI real, dispararíamos uma Task. 
        # Aqui simulamos a execução do agente orquestrador.
        resposta_agente = "Simulação: O paciente Rodrigo possui Ferritina 12 (Baixa). O Oracle sugere o protocolo de Maria (Sucesso). Deseja gerar o rascunho?"
        
        # 3. Salvar novo contexto
        if r:
            novo_contexto = f"{contexto}\nDr: {data.text}\nNSS: {resposta_agente}"
            r.set(f"nss:chat:session:{data.session_id}", novo_contexto[-2000:], ex=3600)
            
        return {
            "resposta": resposta_agente,
            "status": "success",
            "correlation_id": correlation_id_ctx.get()
        }
        
    except Exception as e:
        logger.error(f"Erro no Command Center: {e}")
        return {"error": str(e)}

@app.get("/paciente/{pct_id}/insights")
def get_patient_insights(pct_id: str):
    """
    Bio-Intelligence Dashboard: Resumo de evolução e desfechos clínicos.
    """
    logger.info(f"Gerando insights de Bio-Intelligence para o paciente {pct_id}.")
    try:
        historico = extrair_historico_clinico(pct_id)
        if not historico:
            return {"status": "novo", "message": "Paciente recém-chegado. Sem dados históricos."}
            
        analise_trend = calcular_gap_objetivo(historico)
        
        return {
            "pct_id": pct_id,
            "total_consultas": len(historico),
            "ultima_atualizacao": historico[-1]["data"],
            "tendencia_clinica": analise_trend,
            "timeline": historico[-3:] # Últimos 3 prontuários
        }
    except Exception as e:
        logger.error(f"Erro ao gerar insights para {pct_id}: {e}")
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """Advanced Health Check com diagnóstico de dependências."""
    indices = get_indices()
    
    # 1. Check Redis
    redis_status = "offline"
    if indices.redis_client:
        try:
            indices.redis_client.ping()
            redis_status = "online"
        except:
            notify_critical_failure("Redis detectado como OFFLINE no Health Check.")
            redis_status = "error"

    # 2. Check Google Auth
    creds = get_creds()
    auth_status = "active" if (creds and not creds.expired) else "needs_onboarding"
    if auth_status == "needs_onboarding":
        notify_critical_failure("Google Auth expirado ou ausente. Requer novo Onboarding.")

    return {
        "status": "healthy" if redis_status == "online" and auth_status == "active" else "degraded",
        "correlation_id": correlation_id_ctx.get(),
        "dependencies": {
            "redis": redis_status,
            "google_auth": auth_status,
            "stateless_mode": indices.redis_client is not None
        },
        "version": "1.2.0-sabla"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
