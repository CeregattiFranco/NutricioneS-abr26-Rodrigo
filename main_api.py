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
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return RedirectResponse(auth_url)

@app.get("/onboarding/google/callback")
def google_callback(request: Request, background_tasks: BackgroundTasks):
    """Recebe o callback do Google, troca pelo token e inicializa os índices."""
    logger.info("Callback do Google recebido. Processando código de autorização.")
    code = request.query_params.get("code")
    if not code:
        logger.error("Código de autorização ausente no callback.")
        return {"error": "Código de autorização não recebido."}
        
    flow = get_auth_flow(redirect_uri=f"{BASE_URL}/onboarding/google/callback")
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
from typing import List
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
    from nutriciones.services.google.sheets.base import inserir_lista_recursos, sheet_name_of_resource_type
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
        
    inserir_lista_recursos(PedidoInsercaoListaRecursos(
        spreadsheet_id=config.GoogleServices.sheet_id_cardapio,
        spreadsheet_name=sheet_name_of_resource_type[ExameLaboratorial],
        recursos=novos_exames,
        serialize=generic_serializer
    ))
    
    # Atualizar indices no Redis (Background) para o Agente ler os novos dados
    background_tasks.add_task(refresh_indices, acknowledge_costly_operation=True)
    
    return {"status": "success", "ingested": len(novos_exames)}

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
