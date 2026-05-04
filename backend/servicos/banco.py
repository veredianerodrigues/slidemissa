#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
banco.py - Banco de cantos (SQLite)
"""

import os
import json
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'banco', 'cantos.db')


def _conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def inicializar():
    """Cria o banco e a tabela se não existirem."""
    with _conectar() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS cantos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                posicao       TEXT NOT NULL,
                nome          TEXT NOT NULL,
                chave         TEXT NOT NULL UNIQUE,
                blocos        TEXT NOT NULL,
                criado_em     TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_posicao ON cantos(posicao)")


def _primeiras_palavras(blocos, n=5):
    """Retorna as primeiras N palavras do primeiro verso do canto."""
    for bloco in blocos:
        for linha in bloco.get('lines', []):
            palavras = linha.strip().split()
            if palavras:
                return ' '.join(palavras[:n])
    return "sem titulo"


def _deserializar_canto(row):
    """Converte uma row do SQLite em dict, desserializando blocos de JSON."""
    d = dict(row)
    d['blocos'] = json.loads(d['blocos']) if d['blocos'] else []
    return d


def salvar_canto(posicao, blocos):
    """Salva ou atualiza um canto no banco."""
    inicializar()
    nome  = _primeiras_palavras(blocos)
    chave = posicao + " — " + nome
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    blocos_json = json.dumps(blocos, ensure_ascii=False)

    with _conectar() as con:
        existente = con.execute(
            "SELECT id FROM cantos WHERE chave = ?", (chave,)
        ).fetchone()

        if existente:
            con.execute("""
                UPDATE cantos SET blocos = ?, atualizado_em = ?
                WHERE chave = ?
            """, (blocos_json, agora, chave))
        else:
            con.execute("""
                INSERT INTO cantos (posicao, nome, chave, blocos, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (posicao, nome, chave, blocos_json, agora, agora))

    return chave


def buscar_todos():
    """Retorna todos os cantos ordenados por posição e nome."""
    inicializar()
    with _conectar() as con:
        rows = con.execute(
            "SELECT id, posicao, nome, chave, blocos, criado_em FROM cantos ORDER BY posicao, nome"
        ).fetchall()
    return [_deserializar_canto(r) for r in rows]


def buscar_por_posicao(posicao):
    """Retorna cantos de uma posição específica."""
    inicializar()
    with _conectar() as con:
        rows = con.execute(
            "SELECT id, posicao, nome, chave, blocos, criado_em FROM cantos WHERE posicao = ? ORDER BY nome",
            (posicao,)
        ).fetchall()
    return [_deserializar_canto(r) for r in rows]


def buscar_posicoes():
    """Retorna lista única de posições cadastradas."""
    inicializar()
    with _conectar() as con:
        rows = con.execute(
            "SELECT DISTINCT posicao FROM cantos ORDER BY posicao"
        ).fetchall()
    return [r['posicao'] for r in rows]


def carregar_blocos(chave):
    """Retorna os blocos de um canto pela chave."""
    inicializar()
    with _conectar() as con:
        row = con.execute(
            "SELECT blocos FROM cantos WHERE chave = ?", (chave,)
        ).fetchone()
    if row:
        return json.loads(row['blocos'])
    return None


def deletar(canto_id):
    """Remove um canto pelo ID."""
    inicializar()
    with _conectar() as con:
        con.execute("DELETE FROM cantos WHERE id = ?", (canto_id,))


def deletar_varios(ids):
    """Remove múltiplos cantos pelos IDs. Retorna o número de cantos deletados."""
    if not ids:
        return 0
    inicializar()
    placeholders = ','.join('?' for _ in ids)
    with _conectar() as con:
        cur = con.execute(f"DELETE FROM cantos WHERE id IN ({placeholders})", ids)
        return cur.rowcount


def buscar_por_id(canto_id):
    """Retorna um canto pelo ID."""
    inicializar()
    with _conectar() as con:
        row = con.execute(
            "SELECT * FROM cantos WHERE id = ?", (canto_id,)
        ).fetchone()
    if row:
        return _deserializar_canto(row)
    return None


def limpar_todos():
    """Remove todos os cantos do banco."""
    inicializar()
    with _conectar() as con:
        cur = con.execute("DELETE FROM cantos")
        return cur.rowcount
