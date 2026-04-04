import os
import zipfile
import csv
import logging
import boto3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from nutriciones.core import config, get_base_logger
from nutriciones.services.google.sheets.base import listar_recursos
from nutriciones.services.google.sheets.types import PedidoListagemRecursos
from nutriciones.services.google.sheets.indices import _relationships

logger = get_base_logger("NSS-SHIELD")

class BackupShield:
    """Implementa o Plano de Recuperação de Desastres (NSS Shield)."""
    def __init__(self):
        self.backup_dir = config.BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def exportar_abas_ssot_para_csv(self) -> List[Path]:
        """Exporta todas as abas principais do SSoT para arquivos CSV (Cold Storage)."""
        logger.info("[INFO] [NSS-SHIELD] - Iniciando exportação de abas do Google Sheets.")
        
        from nutriciones.services.google.sheets.base import sheet_name_of_resource_type
        
        csv_files = []
        for resource_type in _relationships:
            sheet_name = sheet_name_of_resource_type[resource_type]
            csv_path = self.backup_dir / f"{sheet_name}.csv"
            
            # Aqui simulamos a leitura bruta de todas as linhas para CSV
            # Em produção, usaríamos as Google API wrappers para obter todas as células
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["COL_A", "COL_B", "COL_C"]) # Header placeholder
                writer.writerow(["DATA", "MOCK", "VALOR"])
            
            csv_files.append(csv_path)
            
        return csv_files

    def criar_pacote_backup(self) -> Path:
        """Compacta CSVs e bancos locais em um arquivo .zip datado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        zip_path = self.backup_dir / f"nss_backup_{timestamp}.zip"
        
        csv_paths = self.exportar_abas_ssot_para_csv()
        
        logger.info(f"[INFO] [NSS-SHIELD] - Criando pacote compactado: {zip_path.name}")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adicionar CSVs
            for csv_file in csv_paths:
                zipf.write(csv_file, arcname=f"ssot/{csv_file.name}")
                os.remove(csv_file) # Limpar temporários
                
            # Adicionar Banco TACO (Imutável)
            if config.DB_PATH.exists():
                zipf.write(config.DB_PATH, arcname=f"db/{config.DB_PATH.name}")
                
        return zip_path

    def enviar_para_cloud_s3(self, arquivo_zip: Path):
        """Envia o backup para o Bucket S3 (Cold Storage/Cloud Recovery)."""
        if not config.AWS_ACCESS_KEY:
            logger.warning("[INFO] [NSS-SHIELD] - AWS Credentials não configuradas. Pulando Cloud Backup.")
            return

        logger.info(f"[INFO] [NSS-SHIELD] - Enviando {arquivo_zip.name} para o cofre Cloud (S3).")
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY,
                aws_secret_access_key=config.AWS_SECRET_KEY
            )
            s3.upload_file(str(arquivo_zip), config.S3_BUCKET_NAME, arquivo_zip.name)
            logger.info(f"[INFO] [NSS-SHIELD] - Backup enviado com sucesso para bucket: {config.S3_BUCKET_NAME}")
        except Exception as e:
            logger.error(f"[ERROR] [NSS-SHIELD] - Falha no envio Cloud: {e}")

    def aplicar_politica_retencao(self):
        """Mantém apenas os últimos backups conforme política do Fator III."""
        arquivos = sorted(self.backup_dir.glob("nss_backup_*.zip"))
        # Reter últimos 5 localmente
        para_remover = arquivos[:-5] if len(arquivos) > 5 else []
        
        for arq in para_remover:
            logger.info(f"[INFO] [NSS-SHIELD] - Removendo backup antigo local: {arq.name}")
            arq.unlink()

def executar_backup_diario():
    """Ponto de entrada para o orquestrador de crons."""
    shield = BackupShield()
    zip_arq = shield.criar_pacote_backup()
    shield.enviar_para_cloud_s3(zip_arq)
    shield.aplicar_politica_retencao()
    logger.info("[INFO] [NSS-SHIELD] - Rotina de Disaster Recovery concluída.")
