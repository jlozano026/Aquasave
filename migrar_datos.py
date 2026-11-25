"""Copia los registros de registros.db (SQLite) a la base PostgreSQL de la nube.

Úsalo una sola vez, desde tu Mac, después de crear la base en Neon:

  DATABASE_URL="postgresql://..." python3 migrar_datos.py
"""
import os
import sqlite3
import sys
from pathlib import Path

import psycopg

url = os.environ.get("DATABASE_URL", "").strip()
db_file = Path(__file__).resolve().parent / "registros.db"
if not url.startswith(("postgres://", "postgresql://")):
    sys.exit("Define DATABASE_URL con la dirección de tu base en la nube.")
if not db_file.exists():
    sys.exit("No encuentro registros.db en esta carpeta.")

import app  # crea las tablas en Postgres si no existen  # noqa: E402,F401

local = sqlite3.connect(db_file)
local.row_factory = sqlite3.Row
with psycopg.connect(url) as cloud:
    for table, cols in [
        ("entries", "full_name, age, apartment, blood_type, visitor_type, entry_date, entry_time"),
        ("enrollments", "class_name, full_name, age, apartment, blood_type, visitor_type, created_at"),
    ]:
        rows = local.execute(f"SELECT {cols} FROM {table} ORDER BY id").fetchall()
        marks = ", ".join(["%s"] * len(cols.split(",")))
        for row in rows:
            cloud.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", tuple(row))
        print(f"{table}: {len(rows)} copiados")
