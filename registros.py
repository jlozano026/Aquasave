"""Consulta, exporta y borra registros desde la terminal.

No tiene contraseña ni página web. Con SQLite se usa en el computador donde corre la app.
Si defines DATABASE_URL (la base de datos en la nube), lee esa base desde cualquier computador.

  python3 registros.py                          ingresos de hoy + todas las inscripciones
  python3 registros.py --fecha 2026-11-28       ingresos de esa fecha + inscripciones
  python3 registros.py --csv                    crea ingresos.csv e inscripciones.csv (abren en Excel)
  python3 registros.py --quitar-ingreso 12      elimina el ingreso con id 12 (por ejemplo, un error)
  python3 registros.py --quitar-inscripcion 5   elimina la inscripción con id 5
"""
import argparse
import csv
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "registros.db"

ENTRY_COLUMNS = [("ID", "id"), ("Fecha", "entry_date"), ("Hora", "entry_time"), ("Nombre", "full_name"),
                 ("Edad", "age"), ("Apartamento", "apartment"), ("RH", "blood_type"), ("Tipo", "visitor_type")]
ENROLLMENT_COLUMNS = [("ID", "id"), ("Clase", "class_name"), ("Nombre", "full_name"), ("Edad", "age"),
                      ("Apartamento", "apartment"), ("RH", "blood_type"), ("Tipo", "visitor_type"),
                      ("Registrado", "created_at")]


DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))


class Db:
    """Misma interfaz para SQLite (local) y PostgreSQL (nube, con DATABASE_URL)."""

    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, params=()):
        if USE_PG:
            sql = sql.replace("?", "%s")
        return self.raw.execute(sql, params)

    def commit(self):
        self.raw.commit()


def connect():
    if USE_PG:
        import psycopg
        from psycopg.rows import dict_row
        return Db(psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row,
                                  connect_timeout=15, prepare_threshold=None))
    if not DB_PATH.exists():
        sys.exit("Todavía no existe registros.db. Inicia la app una vez con: python3 app.py")
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return Db(connection)


def show(title, rows, columns):
    print(f"\n{title} ({len(rows)})")
    if not rows:
        print("  — sin registros —")
        return
    widths = [max(len(head), *(len(str(row[key])) for row in rows)) for head, key in columns]
    print("  " + "  ".join(head.ljust(w) for (head, _), w in zip(columns, widths)))
    print("  " + "  ".join("-" * w for w in widths))
    for row in rows:
        print("  " + "  ".join(str(row[key]).ljust(w) for (_, key), w in zip(columns, widths)))


def export_csv(filename, rows, columns):
    path = BASE_DIR / filename
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([head for head, _ in columns])
        for row in rows:
            writer.writerow([row[key] for _, key in columns])
    print(f"Creado: {path}")


def delete_row(db, table, row_id, done, missing):
    changed = db.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,)).rowcount
    db.commit()
    print(done if changed else missing)


def main():
    parser = argparse.ArgumentParser(description="Consulta los registros de AQUASAVE.")
    parser.add_argument("--fecha", help="fecha de los ingresos a mostrar (AAAA-MM-DD); por defecto, hoy")
    parser.add_argument("--csv", action="store_true", help="exporta todo a archivos CSV")
    parser.add_argument("--quitar-ingreso", type=int, metavar="ID", help="elimina un ingreso por su id")
    parser.add_argument("--quitar-inscripcion", type=int, metavar="ID", help="elimina una inscripción por su id")
    args = parser.parse_args()

    db = connect()

    if args.quitar_ingreso is not None:
        delete_row(db, "entries", args.quitar_ingreso, "Ingreso eliminado.", "No existe un ingreso con ese id.")
        return

    if args.quitar_inscripcion is not None:
        delete_row(db, "enrollments", args.quitar_inscripcion,
                   "Inscripción eliminada.", "No existe una inscripción con ese id.")
        return

    if args.csv:
        export_csv("ingresos.csv", db.execute(
            "SELECT * FROM entries ORDER BY entry_date, entry_time, id").fetchall(), ENTRY_COLUMNS)
        export_csv("inscripciones.csv", db.execute(
            "SELECT * FROM enrollments ORDER BY class_name, full_name").fetchall(), ENROLLMENT_COLUMNS)
        return

    day = args.fecha or datetime.now(ZoneInfo("America/Bogota")).date().isoformat()
    entries = db.execute("SELECT * FROM entries WHERE entry_date = ? ORDER BY entry_time, id", (day,)).fetchall()
    show(f"Ingresos del {day}", entries, ENTRY_COLUMNS)
    if entries:
        residents = sum(1 for row in entries if row["visitor_type"] == "residente")
        print(f"\n  Residentes: {residents} · Invitados: {len(entries) - residents}")

    show("Inscripciones a clases", db.execute(
        "SELECT * FROM enrollments ORDER BY class_name, full_name").fetchall(), ENROLLMENT_COLUMNS)


if __name__ == "__main__":
    main()
