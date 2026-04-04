import functools
import logging
import sys
import traceback
from nutriciones.core import config, get_base_logger
from nutriciones.services.google.gmail import enviar_email_template

logger = get_base_logger("NSS-TELEMETRY")

def monitor_execution(func):
    """
    Decorador para telemetria e tratativa de erros críticos. (Dead Man's Snitch)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"FALHA CRÍTICA NA EXECUÇÃO: {func.__name__}\n{traceback.format_exc()}"
            
            # 1. Log Centralizado (Papertrail via SysLogHandler configurado no core)
            logger.critical(error_msg)
            
            # 2. Notificação Direta por E-mail (Se configurado)
            if config.ADMIN_EMAIL:
                try:
                    enviar_email_template(
                        destinatario=config.ADMIN_EMAIL,
                        assunto=f"[NSS-ALERTA] Falha na Automação: {func.__name__}",
                        template="erro_critico",
                        contexto={
                            "funcao": func.__name__,
                            "erro": str(e),
                            "traceback": traceback.format_exc()
                        }
                    )
                except Exception as email_err:
                    logger.error(f"Não foi possível enviar e-mail de alerta: {email_err}")
            
            # Permitir que a exceção suba se necessário, ou silenciar dependendo da política
            raise
            
    return wrapper
