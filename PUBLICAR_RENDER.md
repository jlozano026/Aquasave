# Publicar AQUASAVE gratis: Render (la app) + Neon (la base de datos)

Render ejecuta la app y Neon guarda los registros. Así los datos no se pierden cuando Render reinicia o duerme la app.
Los planes gratuitos cambian: confirma los límites actuales en render.com y neon.tech al registrarte.

## 1. Crea la base de datos en Neon
1. Entra a https://neon.tech y crea una cuenta (con Google o GitHub).
2. Crea un proyecto: nombre `aquasave`. Elige la región más cercana (por ejemplo AWS US East).
3. En el panel del proyecto pulsa **Connect**. Si ves la opción **Connection pooling**, desactívala.
4. Copia la cadena de conexión. Empieza con `postgresql://` y termina con `?sslmode=require`. **Guárdala: es tu contraseña, no la compartas.**

## 2. Sube el código a GitHub (privado)
1. Crea una cuenta en https://github.com y pulsa **New repository**. Nombre `aquasave`, marca **Private**.
2. Pulsa **uploading an existing file** y arrastra el contenido de esta carpeta (incluye `templates` y `static`).
   No subas `registros.db` ni `venv` (el archivo `.gitignore` ya los excluye si usas Git; si arrastras a mano, déjalos fuera).
3. Pulsa **Commit changes**.

## 3. Publica en Render
1. Entra a https://render.com y crea una cuenta con tu GitHub.
2. **New +** → **Blueprint** → elige el repositorio `aquasave` (autoriza el acceso si lo pide).
3. Render lee `render.yaml` y te pide el valor de `DATABASE_URL`: pega la cadena de Neon del paso 1.
4. Pulsa **Apply** y espera a que termine el despliegue (unos minutos).
5. Tu enlace será algo como `https://aquasave.onrender.com`. Ábrelo desde el celular, con datos móviles.

## 4. Pasar tus registros actuales (opcional)
Solo si ya tienes ingresos en `registros.db` que quieres conservar. Desde tu Mac, en la carpeta del proyecto:
```bash
source venv/bin/activate
pip install -r requirements.txt
DATABASE_URL="pega-aquí-la-cadena-de-neon" python3 migrar_datos.py
```

## 5. Ver y exportar los registros
Desde tu Mac, con el mismo comando y la cadena de Neon:
```bash
DATABASE_URL="..." python3 registros.py              # ingresos de hoy + inscripciones
DATABASE_URL="..." python3 registros.py --csv        # crea los CSV para Excel
DATABASE_URL="..." python3 registros.py --quitar-ingreso 12
```
También puedes verlos en el panel de Neon, sección **Tables** → `entries` y `enrollments`.

## Cosas que debes saber
- **La app se duerme** tras 15 minutos sin visitas y la primera persona espera cerca de 1 minuto. Opcional: un monitor gratuito como UptimeRobot que abra tu enlace cada 5 minutos la mantiene despierta.
- **Haz copias:** exporta los CSV cada semana. En planes gratuitos las copias de seguridad son limitadas.
- **Sin contraseña:** cualquiera con el enlace puede registrar datos. Compártelo solo con residentes (por ejemplo, con un QR en la entrada).
- **Datos personales de menores y RH:** publica una política de tratamiento de datos (Ley 1581 de 2012).
- **Uso local:** sin `DATABASE_URL` la app sigue usando `registros.db` en tu computador, como antes.
