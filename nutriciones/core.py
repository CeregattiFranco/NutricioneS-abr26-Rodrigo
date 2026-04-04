import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import logging
from logging.handlers import SysLogHandler

import contextvars
import requests

# Contexto para Correlation ID (Fator XI)
correlation_id_ctx = contextvars.ContextVar("correlation_id", default="NSS-SYSTEM")

class Config:
    environment = os.getenv("NUTRICIONES_ENV", "dev")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    PAPERTRAIL_HOST = os.getenv("PAPERTRAIL_HOST", "")
    PAPERTRAIL_PORT = int(os.getenv("PAPERTRAIL_PORT", "0"))
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

    class Google:
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    class GoogleServices:
        sheet_id_cardapio = os.environ.get("GOOGLE_SHEET_ID_CARDAPIO", "")
        doc_template_id = os.environ.get("GOOGLE_DOC_TEMPLATE_ID", "")
        calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "")
        nutriciones_folder_id = os.environ.get("GOOGLE_DRIVE_FILE_ID", "")
        exams_sheet_template_id = os.environ.get("GOOGLE_EXAMS_SHEET_TEMPLATE_ID", "")

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
    FATHOM_API_KEY = os.environ.get("FATHOM_API_KEY", "")
    FATHOM_WEBHOOK_SECRET = os.environ.get("FATHOM_WEBHOOK_SECRET", "")
    
    # NSS Shield - Cloud Backups (S3)
    AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY", "")
    AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY", "")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "nss-backups")
    BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    BACKUP_DIR = BASE_DIR / "backups"
    DB_PATH = DATA_DIR / "taco.sqlite"
    TACO_JSON_PATH = DATA_DIR / "taco.json"

config = Config()

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_ctx.get()
        return True

def notify_critical_failure(message: str):
    """Dispara alerta via Webhook para Slack/Discord."""
    if config.SLACK_WEBHOOK_URL:
        try:
            payload = {"text": f"🚨 *NSS-ALERTA CRÍTICO*\n> {message}"}
            requests.post(config.SLACK_WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            logging.error(f"Falha ao enviar webhook: {e}")

def get_base_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Correlation Filter
        corr_filter = CorrelationIdFilter()
        logger.addFilter(corr_filter)

        # Stream Handler (Local/Docker)
        stream_formatter = logging.Formatter('[%(levelname)s] [%(name)s] [%(correlation_id)s] - %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(stream_formatter)
        logger.addHandler(sh)
        
        # Papertrail Handler (Remote)
        if config.PAPERTRAIL_HOST and config.PAPERTRAIL_PORT:
            try:
                from syslog_rfc5424_formatter import RFC5424Formatter
                
                syslog_formatter = RFC5424Formatter(
                    msgid="NSS-PROD",
                    appname=name
                )
                
                handler = SysLogHandler(address=(config.PAPERTRAIL_HOST, config.PAPERTRAIL_PORT))
                handler.setFormatter(syslog_formatter)
                logger.addHandler(handler)
            except Exception as e:
                logger.warning(f"Falha ao configurar Papertrail: {e}")
                
    return logger

logger = get_base_logger("NSS-CORE")
