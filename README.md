# AQUASAVE — Registro de ingreso e inscripciones (Flask)

Páginas para registrar datos **sin reservas, sin cuentas, sin contraseñas y sin niveles de usuario**: todos ven lo mismo.

## Menú principal
- **Registro de ingreso**: nombre, edad, apartamento, RH y si es residente o invitado. La fecha y la hora de ingreso se guardan solas (hora de Colombia).
- **Nuestras clases**: natación niños, natación adultos, aquagimnasia y zumba. Se inscribe con los mismos datos.

## Horario de atención
- Martes a viernes: 4:00 p. m. a 8:00 p. m.
- Sábados y domingos: 9:00 a. m. a 7:00 p. m.
- Almuerzo (sábados y domingos): 12:00 p. m. a 1:00 p. m., sin servicio
- Lunes: cerrado

Es solo informativo: se muestra en la página de ingreso y no bloquea el registro.
Para cambiarlo, o para editar las clases y las opciones de RH, usa la sección **CONFIGURACIÓN** de `app.py`
(`OPEN_HOURS`, `BLOOD_TYPES`, `VISITOR_TYPES`, `CLASSES`).

## Instalación en Mac
```bash
cd ~/Downloads
unzip AQUASAVE_RESERVAS.zip
cd AQUASAVE_RESERVAS

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```
Abre `http://127.0.0.1:5000`. La base de datos (`registros.db`) se crea sola.

## Dónde quedan guardados los ingresos
En el archivo `registros.db` (SQLite), en la misma carpeta que `app.py`: tabla `entries` (ingresos, con fecha y hora de Colombia) y tabla `enrollments` (inscripciones).

## Ver los registros (sin contraseña)
La página web solo sirve para ingresar datos. Para consultarlos, usa el script en el mismo computador donde corre la app:

```bash
python3 registros.py                          # ingresos de hoy + todas las inscripciones
python3 registros.py --fecha 2026-11-28       # ingresos de otra fecha
python3 registros.py --csv                    # crea ingresos.csv e inscripciones.csv (abren en Excel)
python3 registros.py --quitar-ingreso 12      # elimina el ingreso con id 12
python3 registros.py --quitar-inscripcion 5   # elimina la inscripción con id 5
```

## Importante
- La base nueva es `registros.db`; los archivos anteriores (`aquasave.db`, `reservas.db`) ya no se usan.
- Se guardan nombres, edades (incluidos menores) y RH. Antes de publicarla en internet usa HTTPS, un servidor como `gunicorn`, respaldos de `registros.db` y una política de tratamiento de datos (Ley 1581 de 2012).

## Publicar en internet
Ver `PUBLICAR_VERCEL.md` (Vercel + Neon) o `PUBLICAR_RENDER.md` (Render + Neon), ambos gratis. Sin la variable `DATABASE_URL` la app usa `registros.db` local.
