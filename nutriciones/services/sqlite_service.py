import sqlite3
import json
import logging
from typing import Optional
from pathlib import Path
from nutriciones.core import config

logger = logging.getLogger(__name__)

def _get_connection() -> sqlite3.Connection:
    needs_init = not config.DB_PATH.exists()
    conn = sqlite3.connect(config.DB_PATH)
    if needs_init:
        # Avoid circular loop, initialize directly
        _init_schema(conn)
        _populate_data(conn)
    return conn

def _init_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            kcal REAL,
            proteina_g REAL,
            lipidios_g REAL,
            carboidratos_g REAL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nome ON alimentos(nome)')
    conn.commit()

def _parse_float_br(val) -> float:
    if not val:
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def _populate_data(conn: sqlite3.Connection):
    if not config.TACO_JSON_PATH.exists():
        logger.warning(f"Arquivo {config.TACO_JSON_PATH} não encontrado. Usando db vazio.")
        return
        
    try:
        with open(config.TACO_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler JSON da TACO: {e}")
        return
        
    cursor = conn.cursor()
    
    for item in data:
        # Pega as chaves reais que importou no JSON. Supondo mesma estrutura de db_alimentos
        nome = item.get("nome", "").strip() or item.get("description", "").strip()
        if not nome:
            continue
            
        kcal = _parse_float_br(item.get("kcal", item.get("energy_kcal", 0)))
        prot = _parse_float_br(item.get("proteina_g", item.get("protein_g", 0)))
        lip = _parse_float_br(item.get("lipidios_g", item.get("lipid_g", 0)))
        carb = _parse_float_br(item.get("carboidratos_g", item.get("carbohydrate_g", 0)))
        
        cursor.execute('''
            INSERT OR IGNORE INTO alimentos (nome, kcal, proteina_g, lipidios_g, carboidratos_g)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, kcal, prot, lip, carb))
        
    conn.commit()
    logger.info("Base de dados SQLite indexada ou atualizada com sucesso.")

from nutriciones.models.alimentos import AlimentoSQLite

def pesquisar_alimento_nome(nome: str) -> list[AlimentoSQLite]:
    """Busca alimentos que contêm a substring no nome (case-insensitive)"""
    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nome, kcal, proteina_g, lipidios_g, carboidratos_g
        FROM alimentos
        WHERE nome LIKE ?
    ''', (f"%{nome}%",))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [AlimentoSQLite(**dict(r)) for r in rows]

def get_alimento_exato(nome: str) -> Optional[AlimentoSQLite]:
    """Busca alimento especificado exato para O(1) query performática"""
    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nome, kcal, proteina_g, lipidios_g, carboidratos_g
        FROM alimentos
        WHERE lower(nome) = lower(?)
    ''', (nome,))
    
    row = cursor.fetchone()
    conn.close()
    
    return AlimentoSQLite(**dict(row)) if row else None
