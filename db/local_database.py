# db/local_database.py
import sqlite3
import os
from datetime import datetime

DB_PATH = "people_counter.db"

def init_db():
    """Buat tabel jika belum ada"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('IN', 'OUT'))
        )
    """)
    conn.commit()
    conn.close()

def insert_count(direction: str):
    """Simpan data IN/OUT"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO counts (timestamp, direction) VALUES (?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), direction)
    )
    conn.commit()
    conn.close()

def get_summary():
    """Ambil total IN dan OUT"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM counts WHERE direction='IN'")
    in_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM counts WHERE direction='OUT'")
    out_count = c.fetchone()[0]
    conn.close()
    return {"in": in_count, "out": out_count}

def get_last_records(limit=10):
    """Ambil data terbaru"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM counts ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
