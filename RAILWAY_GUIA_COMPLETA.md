# 🚀 GUÍA COMPLETA: DESPLIEGUE EN RAILWAY

## Índice
1. [Preparación Local](#preparación-local)
2. [Crear Cuenta en Railway](#crear-cuenta-en-railway)
3. [Desplegar la Base de Datos](#desplegar-la-base-de-datos)
4. [Desplegar el Bot](#desplegar-el-bot)
5. [Configurar Variables](#configurar-variables)
6. [Monitoreo](#monitoreo)
7. [Solución de Problemas](#solución-de-problemas)

---

## Preparación Local

### Paso 1: Instalar PostgreSQL Localmente (Opcional)

Si quieres probar localmente antes de subir a Railway:

**Windows:**
- Descarga: https://www.postgresql.org/download/windows/
- Instala con contraseña segura
- Asegúrate de instalar pgAdmin (herramienta gráfica)

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Paso 2: Crear Base de Datos Local

```bash
# Conectar como usuario postgres
psql -U postgres

# Crear la base de datos
CREATE DATABASE rifas_bot;

# Salir
\q
```

### Paso 3: Configurar Variables Locales

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Abre `.env` y reemplaza los valores:

```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/rifas_bot
TOKEN=1234567890:ABCDefghijklmnop_QRSTUV-WxyzabCDEFG
ADMIN_ID=123456789
GRUPO_RIFAS_ID=-1001234567890
```

Para obtener:
- **TOKEN**: Habla con [@BotFather](https://t.me/botfather) en Telegram → /newbot
- **TU_ID**: Escribe a [@userinfobot](https://t.me/userinfobot)
- **GRUPO_ID**: Agrega el bot al grupo, envía un mensaje, ve los logs

### Paso 4: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 5: Probar Localmente (Opcional)

```bash
python bot.py
```

Si dice "🤖 Bot corriendo..." entonces ¡éxito! 🎉

---

## Crear Cuenta en Railway

### Paso 1: Registrarse

1. Ve a https://railway.app
2. Click en "Start Building Now"
3. Elige "Continue with GitHub"
4. Autoriza Railway a acceder a tu GitHub
5. Crea una cuenta o inicia sesión

### Paso 2: Crear Nuevo Proyecto

1. En el dashboard, click "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Si no has conectado GitHub, autoriza ahora
4. Busca y selecciona `telegram-rifas-bot`

> ℹ️ Si no ves tu repositorio, puede que necesites crear uno primero:
> - Ve a GitHub.com → New repository
> - Nombre: `telegram-rifas-bot`
> - Sube tu código: `git push origin main`

---

## Desplegar la Base de Datos

### Opción A: Desde el Dashboard (Recomendado)

1. En tu proyecto Railway, haz click en "Add Service"
2. Click en "Add from marketplace"
3. Busca **PostgreSQL**
4. Click en PostgreSQL → Click "Add"
5. ¡Listo! Railway crea automáticamente `DATABASE_URL`

### Opción B: Desde la CLI

```bash
# Instalar CLI de Railway
npm install -g @railway/cli

# Login
railway login

# Agregar PostgreSQL
railway service add postgresql
```

### Verificar PostgreSQL está activo

En el dashboard:
1. Selecciona el servicio PostgreSQL
2. Verifica que esté "Running" (verde)
3. Copia la URL de `DATABASE_URL` (sin hacer nada, solo verifica que existe)

---

## Desplegar el Bot

### Paso 1: Configurar Deploy Automático

1. En Railway, selecciona tu servicio del bot
2. Ve a "Settings" → "Deploy"
3. En "Deploy on Push" selecciona **ON**
4. Rama: `main` (o la que uses)

✅ Ahora cada vez que hagas `git push`, Railway despliega automáticamente

### Paso 2: Configurar Variables de Entorno

1. En Railway, selecciona el servicio del bot (Python)
2. Ve a "Variables"
3. Agrega estas variables:

```
TOKEN=1234567890:ABCDefghijklmnop_QRSTUV-WxyzabCDEFG
ADMIN_ID=123456789
GRUPO_RIFAS_ID=-1001234567890
```

> ℹ️ `DATABASE_URL` se agrega automáticamente desde PostgreSQL

### Paso 3: Primer Deploy

1. Haz cambios menores (ej. actualiza README)
2. Haz un commit:
```bash
git add .
git commit -m "Deploy inicial en Railway"
git push origin main
```
3. Abre Railway y ve los logs
4. Deberías ver "🤖 Bot corriendo..."

---

## Configurar Variables

### ¿Dónde obtener cada variable?

#### TOKEN
1. Abre Telegram
2. Habla con [@BotFather](https://t.me/botfather)
3. Escribe: `/newbot`
4. Dame un nombre (ej: "Mi Rifa Bot")
5. Dame un username (ej: `mi_rifa_bot`)
6. ¡Recibirás el TOKEN!

Ejemplo:
```
🎉 Done! Congratulations on your new bot. You will find it at t.me/mi_rifa_bot. 
You can now add a description, about section and profile picture for your bot, see /help for a list of commands.

Use this token to access the HTTP API:
1234567890:ABCDefghijklmnop_QRSTUV-WxyzabCDEFG
```

#### ADMIN_ID
1. Abre Telegram
2. Habla con [@userinfobot](https://t.me/userinfobot)
3. Te mostrará tu ID

#### GRUPO_RIFAS_ID
1. Crea un grupo nuevo en Telegram
2. Agrega tu bot al grupo (invítalo)
3. Envía un mensaje en el grupo
4. Abre esta URL en tu navegador:
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
5. Reemplaza `<TOKEN>` con tu token
6. Busca `"chat":{"id":-1001234567890` (es un número negativo grande)

---

## Monitoreo

### Ver Logs en Tiempo Real

**Desde Railway Web:**
1. Ve a tu proyecto
2. Selecciona el servicio del bot
3. Click en "Logs"
4. Verás todo lo que imprime el bot

**Desde CLI:**
```bash
railway login
railway logs -f  # -f para seguimiento en vivo
```

### Soluciones Rápidas

**El bot no se inicia:**
- Abre Logs y busca errores
- Verifica que todas las variables estén configuradas
- Revisa que PostgreSQL esté corriendo

**"DATABASE_URL not found":**
- Ve que PostgreSQL esté agregado
- Espera 30 segundos y recarga
- Si no aparece, agrega manualmente:
```
postgresql://user:password@host:port/database
```

**El bot se para de repente:**
1. Abre Logs
2. Busca mensajes de error
3. Reinicia: Settings → Restart Service

---

## Solución de Problemas

### Error: "No module named 'psycopg2'"

**Solución:**
- Verifica que `requirements.txt` tenga `psycopg2-binary==2.9.9`
- Haz un commit y push para que Railway reinstale

### Error: "CONNECTION REFUSED"

**Posible causa:** PostgreSQL no está corriendo

**Solución:**
1. Abre Railway
2. Ve al servicio PostgreSQL
3. Verifica que esté en estado "Running" (verde)
4. Si está rojo, click en "Restart Service"

### Error: "FATAL: database 'rifas_bot' does not exist"

**Solución:**
Railway crea la BD automáticamente con PostgreSQL. Si no:
1. Haz un deploy nuevamente
2. Espera a que se ejecute `init_db()`

### El bot recibe comandos pero no responde

**Posibles causas:**
1. TOKEN incorrecto
2. Bot no está habilitado para grupos
3. Firewall bloqueando

**Soluciones:**
1. Verifica TOKEN en [@BotFather](https://t.me/botfather)
2. En [@BotFather](/setprivacy) → Desactiva "Privacy Mode"
3. Ve los logs para ver si hay mensajes de error

### "Chat not found"

**Causa:** ADMIN_ID o GRUPO_RIFAS_ID son incorrectos

**Solución:**
1. Usa [@userinfobot](https://t.me/userinfobot) para obtener tu ID correcto
2. Actualiza ADMIN_ID en Railway
3. Para GRUPO_RIFAS_ID, usa la URL de getUpdates

---

## Checklist Final

Antes de decir que está "listo":

- [ ] Cuenta en Railway creada
- [ ] Repositorio en GitHub
- [ ] PostgreSQL agregado a Railway
- [ ] Variables configuradas (TOKEN, ADMIN_ID, GRUPO_RIFAS_ID)
- [ ] Bot desplegado (estado "Running")
- [ ] Bot responde a `/start` en Telegram
- [ ] Admin puede crear rifas con `/crearrifa`
- [ ] Puedes seleccionar números y comprar
- [ ] Admin recibe comprobantes de pago

---

## Mantenimiento

### Actualizar el Bot

```bash
# Realizar cambios en el código
git add .
git commit -m "Descripción de cambios"
git push origin main
# ¡Railway redeploya automáticamente!
```

### Respaldar la Base de Datos

Railway proporciona backups automáticos:
1. Ve al servicio PostgreSQL
2. Tab "Backups"
3. Verás backups automáticos de 7 días

### Ver uso de recursos

1. Selecciona tu servicio
2. Tab "Metrics"
3. Verás CPU, memoria, etc.

---

## Cambiar a Webhook (Avanzado)

Por defecto, el bot usa **polling** (preguntar continuamente). 
Para mejor rendimiento, puedes usar **webhook** (escuchar):

```bash
# Configurar webhook (desde tu máquina)
curl -X POST \
  "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://tu-proyecto-railway.up.railway.app/webhook" \
  -d "drop_pending_updates=true"

# Verificar
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

Reemplaza:
- `<TOKEN>` con tu token
- `tu-proyecto-railway.up.railway.app` con el dominio de Railway

---

## 🎉 ¡Listo!

Tu bot de rifas está en vivo en Internet 24/7 en Railway.

Cualquier problema, revisa los logs o las secciones de troubleshooting arriba.

**¡Mucha suerte con tu bot! 🚀**
