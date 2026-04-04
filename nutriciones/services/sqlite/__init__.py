import sqlite3
import json
import logging
from typing import Optional
from pathlib import Path
from nutriciones.core import config
from nutriciones.models.alimentos import AlimentoSQLite

logger = logging.getLogger(__name__)

def alimento_factory(row: tuple) -> AlimentoSQLite:
    """Converte uma linha do SQLite diretamente para o modelo AlimentoSQLite."""
    return AlimentoSQLite(
        nome=row[0],
        kcal=row[1],
        proteina_g=row[2],
        lipidios_g=row[3],
        carboidratos_g=row[4]
    )

def get_connection() -> sqlite3.Connection:
    needs_init = not config.DB_PATH.exists()
    conn = sqlite3.connect(config.DB_PATH)
    if needs_init:
        init_schema(conn)
    return conn

def init_schema(conn: sqlite3.Connection):
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

def pesquisar_alimento_nome(termo: str) -> list[AlimentoSQLite]:
    """Busca alimentos que contêm o termo no nome (case-insensitive)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nome, kcal, proteina_g, lipidios_g, carboidratos_g
        FROM alimentos
        WHERE nome LIKE ?
    ''', (f"%{termo}%",))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [alimento_factory(r) for r in rows]

def get_alimento_exato(nome: str) -> Optional[AlimentoSQLite]:
    """Busca alimento especificado exato para O(1) query performática"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nome, kcal, proteina_g, lipidios_g, carboidratos_g
        FROM alimentos
        WHERE lower(nome) = lower(?)
    ''', (nome,))
    
    row = cursor.fetchone()
    conn.close()
    
    return alimento_factory(row) if row else None
