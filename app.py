import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, flash, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "registros.db"
TZ = ZoneInfo("America/Bogota")

# ---------------------------------------------------------------------------
# CONFIGURACIÓN (aquí ajustas horarios, clases y opciones)
# ---------------------------------------------------------------------------

# Horario de atención. Es solo informativo: se muestra en la página de ingreso.
OPEN_HOURS = [
    ("Martes a viernes", "4:00 p. m. a 8:00 p. m."),
    ("Sábados y domingos", "9:00 a. m. a 7:00 p. m."),
    ("Almuerzo (sábados y domingos)", "12:00 p. m. a 1:00 p. m., sin servicio"),
    ("Lunes", "cerrado"),
]

BLOOD_TYPES = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-", "No sé"]
VISITOR_TYPES = {"residente": "Residente", "invitado": "Invitado"}

CLASSES = [
    {
        "slug": "natacion-ninos",
        "color": "#ff8a3d",
        "name": "Natación niños",
        "day": "Domingo",
        "time": "10:00 a. m. – 11:00 a. m.",
        "description": "Aprendizaje y formación acuática para niños.",
        "icon": "🏊"
    },
    {
        "slug": "natacion-adultos",
        "color": "#1fb5d4",
        "name": "Natación adultos",
        "day": "Sábado",
        "time": "11:00 a. m. – 12:00 p. m.",
        "description": "Técnica, aprendizaje y acondicionamiento.",
        "icon": "🏊‍♀️"
    },
    {
        "slug": "aquagimnasia",
        "color": "#7a5cff",
        "name": "Aquagimnasia",
        "day": "Sábado",
        "time": "10:00 a. m. – 11:00 a. m.",
        "description": "Actividad física y bienestar dentro del agua.",
        "icon": "💧"
    },
    {
        "slug": "zumba",
        "color": "#ff4f8b",
        "name": "Zumba",
        "day": "Viernes",
        "time": "7:00 p. m. – 8:00 p. m.",
        "description": "Baile, música y actividad física.",
        "icon": "🎶"
    },
]

DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTH_NAMES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
               "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ---------------------------------------------------------------------------
# Clave secreta (se genera sola la primera vez; también puedes usar SECRET_KEY)
# ---------------------------------------------------------------------------
def load_secret_key():
    value = os.environ.get("SECRET_KEY")
    if value:
        return value
    path = BASE_DIR / ".secret_key"
    if not path.exists():
        path.write_text(secrets.token_hex(32), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


# Los archivos estáticos viven en public/static: Vercel los sirve desde public/ y Flask (local) desde la misma carpeta.
app = Flask(__name__, static_folder="public/static")
app.secret_key = load_secret_key()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("HTTPS") == "1")  # HTTPS=1 al publicar en internet
app.jinja_env.globals["blood_types"] = BLOOD_TYPES


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------
def long_date(d):
    return f"{DAY_NAMES[d.weekday()]} {d.day} de {MONTH_NAMES[d.month - 1]} de {d.year}"


def time_label(moment):
    suffix = "a. m." if moment.hour < 12 else "p. m."
    return f"{moment.hour % 12 or 12}:{moment.minute:02d}\u00a0{suffix.replace(' ', chr(160))}"


def open_status(now):
    """Informativo: indica si la piscina está en horario de atención ahora."""
    weekday, minute = now.weekday(), now.hour * 60 + now.minute
    at = lambda h: time_label(now.replace(hour=h, minute=0))
    if weekday == 0:
        return False, "Hoy lunes estamos cerrados. Abrimos mañana a las 4:00 p. m."
    opens, closes = (16, 20) if weekday <= 4 else (9, 19)
    if minute < opens * 60:
        return False, f"Cerrado por ahora. Abrimos hoy a las {at(opens)}"
    if minute >= closes * 60:
        return False, "Cerrado por hoy. ¡Hasta la próxima!"
    if weekday >= 5 and 12 * 60 <= minute < 13 * 60:
        return False, f"Hora de almuerzo. Volvemos a las {at(13)}"
    return True, f"Abierto ahora. Cerramos a las {at(closes)}"


@app.context_processor
def inject_today():
    """Fecha de hoy (hora de Colombia) disponible en todas las páginas."""
    now = datetime.now(TZ)
    return {"today_label": long_date(now).capitalize(), "today_iso": now.date().isoformat(),
            "now_label": time_label(now), "open_now": open_status(now)[0], "open_text": open_status(now)[1]}


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
# Si existe la variable DATABASE_URL se usa PostgreSQL (nube); si no, SQLite local (registros.db).
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))
if USE_PG:
    import psycopg
    from psycopg.rows import dict_row


class Db:
    """Misma interfaz para SQLite y PostgreSQL: execute(sql, params) con marcadores ?."""

    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, params=()):
        if USE_PG:
            sql = sql.replace("?", "%s")
        return self.raw.execute(sql, params)


@contextmanager
def db_connection():
    if USE_PG:
        raw = psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row,
                              connect_timeout=15, prepare_threshold=None)
    else:
        raw = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
        raw.row_factory = sqlite3.Row
    try:
        yield Db(raw)
    finally:
        raw.close()


@contextmanager
def write_transaction():
    """Bloquea las escrituras mientras se revisa y se guarda."""
    with db_connection() as db:
        if USE_PG:
            with db.raw.transaction():
                db.execute("SELECT pg_advisory_xact_lock(7001)")
                yield db
            return
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
        except Exception:
            db.execute("ROLLBACK")
            raise
        else:
            db.execute("COMMIT")


def init_db():
    id_col = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    statements = [
        f"""CREATE TABLE IF NOT EXISTS entries (
                id {id_col},
                full_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                apartment TEXT NOT NULL,
                blood_type TEXT NOT NULL,
                visitor_type TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                entry_time TEXT NOT NULL
            )""",
        "CREATE INDEX IF NOT EXISTS idx_entries_date ON entries (entry_date)",
        f"""CREATE TABLE IF NOT EXISTS enrollments (
                id {id_col},
                class_name TEXT NOT NULL,
                full_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                apartment TEXT NOT NULL,
                blood_type TEXT NOT NULL,
                visitor_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""",
    ]
    with write_transaction() as db:
        for statement in statements:
            db.execute(statement)


init_db()  # se ejecuta siempre: con python app.py, flask run o gunicorn


# ---------------------------------------------------------------------------
# Protección CSRF (sin dependencias extra)
# ---------------------------------------------------------------------------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("_csrf", "").encode()
        expected = session.get("_csrf", "").encode()
        if not expected or not secrets.compare_digest(sent, expected):
            flash("Tu sesión expiró. Vuelve a intentarlo.", "error")
            return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Validación de los datos (igual para ingresos e inscripciones)
# ---------------------------------------------------------------------------
def read_person(form):
    """Devuelve (datos, None) o (None, mensaje de error)."""
    name = " ".join(form["nombre"].split())
    apartment = " ".join(form["apartamento"].split())
    blood_type = form["rh"]
    visitor_type = form["tipo"]
    try:
        age = int(form["edad"])
    except ValueError:
        age = 0

    if not name or not apartment or not blood_type or not visitor_type:
        return None, "Completa todos los campos."
    if len(name) > 80 or len(apartment) > 20:
        return None, "El nombre o el apartamento son demasiado largos."
    if not 1 <= age <= 109:
        return None, "La edad debe estar entre 1 y 109 años."
    if blood_type not in BLOOD_TYPES:
        return None, "Selecciona un RH válido."
    if visitor_type not in VISITOR_TYPES:
        return None, "Indica si eres residente o invitado."

    return {"name": name, "apartment": apartment, "age": age,
            "blood_type": blood_type, "visitor_type": visitor_type}, None


def same_person(row, person):
    return (row["full_name"].casefold() == person["name"].casefold()
            and row["apartment"].casefold() == person["apartment"].casefold())


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Registro de ingreso
# ---------------------------------------------------------------------------
def save_entry(form):
    """Valida y guarda. Devuelve un mensaje de error, o None si quedó guardado."""
    person, error = read_person(form)
    if error:
        return error

    now = datetime.now(TZ)
    with db_connection() as db:
        db.execute("""
            INSERT INTO entries
            (full_name, age, apartment, blood_type, visitor_type, entry_date, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (person["name"], person["age"], person["apartment"], person["blood_type"],
              person["visitor_type"], now.date().isoformat(), now.strftime("%H:%M:%S")))

    flash(f"¡Ingreso registrado, {person['name'].split()[0]}! "
          f"{long_date(now).capitalize()}, {time_label(now)}", "success")
    return None


@app.route("/ingreso", methods=["GET", "POST"])
def ingreso():
    form = {"nombre": "", "edad": "", "apartamento": "", "rh": "", "tipo": ""}
    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        error = save_entry(form)
        if error is None:
            return redirect(url_for("ingreso"))
        flash(error, "error")

    return render_template("ingreso.html", form=form, schedule=OPEN_HOURS)


# ---------------------------------------------------------------------------
# Clases
# ---------------------------------------------------------------------------
def save_enrollment(selected_class, form):
    """Valida y guarda. Devuelve un mensaje de error, o None si quedó guardada."""
    person, error = read_person(form)
    if error:
        return error

    with write_transaction() as db:
        rows = db.execute("""
            SELECT full_name, apartment FROM enrollments WHERE class_name = ?
        """, (selected_class["name"],)).fetchall()

        if any(same_person(r, person) for r in rows):
            return "Ya hay una inscripción con ese nombre y apartamento en esta clase."
        db.execute("""
            INSERT INTO enrollments
            (class_name, full_name, age, apartment, blood_type, visitor_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (selected_class["name"], person["name"], person["age"], person["apartment"],
              person["blood_type"], person["visitor_type"],
              datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")))

    flash(f"¡Inscripción registrada, {person['name'].split()[0]}! {selected_class['name']} · "
          f"{selected_class['day']}, {selected_class['time']}.", "success")
    return None


@app.route("/clases")
def clases():
    return render_template("clases.html", classes=CLASSES)


@app.route("/inscripcion/<slug>", methods=["GET", "POST"])
def inscripcion(slug):
    selected_class = next((c for c in CLASSES if c["slug"] == slug), None)
    if selected_class is None:
        return redirect(url_for("clases"))

    form = {"nombre": "", "edad": "", "apartamento": "", "rh": "", "tipo": ""}
    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        error = save_enrollment(selected_class, form)
        if error is None:
            return redirect(url_for("clases"))
        flash(error, "error")

    return render_template("inscripcion.html", selected_class=selected_class, form=form)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
