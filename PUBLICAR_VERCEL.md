# Publicar AQUASAVE gratis: Vercel (la app) + Neon (la base de datos)

Vercel no guarda archivos entre visitas, así que la base de datos TIENE que ser externa (Neon). La app no se "duerme" como en Render.
Confirma los límites del plan gratuito en vercel.com y neon.tech: el plan Hobby de Vercel está pensado para uso personal y no comercial, revisa sus términos.

## 1. Base de datos (Neon)
Igual que en `PUBLICAR_RENDER.md`, paso 1: crea el proyecto y copia la cadena `postgresql://...?sslmode=require`.

## 2. Código en GitHub (privado)
Igual que en `PUBLICAR_RENDER.md`, paso 2. Sube todo el contenido de la carpeta, incluida `public/`. No subas `registros.db`.

## 3. Publica en Vercel
1. Entra a https://vercel.com y crea una cuenta con tu GitHub.
2. **Add New… → Project** → importa el repositorio `aquasave`.
3. Vercel detecta Flask solo (busca `app.py`). No cambies el comando de build.
4. Abre **Environment Variables** y agrega tres:
   - `DATABASE_URL` = la cadena de Neon
   - `SECRET_KEY` = un texto largo al azar. Para generarlo, en tu Mac: `python3 -c "import secrets; print(secrets.token_hex(32))"`
   - `HTTPS` = `1`
5. Pulsa **Deploy**. Tu enlace será algo como `https://aquasave.vercel.app`.

Si cambias una variable después, haz un nuevo despliegue (Deployments → Redeploy) para que se aplique.

## 4. Ver y exportar los registros
Igual que en `PUBLICAR_RENDER.md`, pasos 4 y 5 (con `DATABASE_URL="..." python3 registros.py`).

## Importante
- Sin `SECRET_KEY` la app intentaría escribir un archivo y fallaría en Vercel.
- Sin `DATABASE_URL` la app usaría SQLite, que en Vercel no guarda nada: ponla siempre.
- Sin contraseña: cualquiera con el enlace puede registrar datos. Compártelo solo con residentes (QR en la entrada).
- Política de tratamiento de datos (Ley 1581 de 2012) por los datos de menores y el RH.
