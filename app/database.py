import sqlite3
from pathlib import Path
from app.config import ROOT

DB_PATH = ROOT / "tuition.db"

def connect(db_path: str | Path = DB_PATH):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database(db_path: str | Path = DB_PATH):
    schema = (ROOT / "app" / "schema.sql").read_text(encoding="utf-8")
    conn = connect(db_path)
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()
