# 📱 Guía de Despliegue en Railway

## Paso 1: Preparar el Entorno Local

### 1.1 Instalar PostgreSQL (si aún no lo tienes)
- **Windows**: Descarga desde https://www.postgresql.org/download/windows/
- **macOS**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql`

### 1.2 Crear base de datos local
```bash
# Conectar a PostgreSQL
psql -U postgres

# Crear base de datos
CREATE DATABASE rifas_bot;
\q
```

### 1.3 Configurar variables de entorno
```bash
# Crea un archivo .env en la raíz del proyecto
copy .env.example .env
```

Edita `.env` con tus valores:
```
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/rifas_bot
TOKEN=tu_token_de_telegram
ADMIN_ID=tu_id_de_telegram
GRUPO_RIFAS_ID=id_del_grupo
```

### 1.4 Instalar dependencias
```bash
pip install -r requirements.txt
```

### 1.5 Migrar datos de SQLite a PostgreSQL
Si tienes datos en la base de datos SQLite anterior:
```bash
python migrate_to_postgresql.py
```

## Paso 2: Desplegar en Railway

### 2.1 Crear cuenta en Railway
1. Ve a https://railway.app
2. Registrate con GitHub (es lo más fácil)
3. Crea un nuevo proyecto

### 2.2 Conectar GitHub
1. En Railway, click en "New Project" → "Deploy from GitHub repo"
2. Autoriza a Railway acceder a tu GitHub
3. Selecciona tu repositorio `telegram-rifas-bot`

### 2.3 Agregar PostgreSQL a Railway

**Opción A: Desde el Dashboard (Recomendado)**
1. Ve a tu proyecto en Railway
2. Click en "Add Service" → "Add from marketplace" → "PostgreSQL"
3. Se crea automáticamente una base de datos

**Opción B: Desde CLI**
```bash
npm install -g @railway/cli
railway login
railway service add postgresql
```

### 2.4 Configurar Variables de Entorno en Railway

En el dashboard de Railway:
1. Selecciona tu servicio del bot
2. Ve a "Variables"
3. Agrega estas variables:
   - `TOKEN`: Tu token de Telegram
   - `ADMIN_ID`: Tu ID de Telegram
   - `GRUPO_RIFAS_ID`: ID del grupo de Telegram
   - `DATABASE_URL`: Se agregar automáticamente desde PostgreSQL

⚠️ **Importante**: Railway genera automáticamente `DATABASE_URL` cuando creas PostgreSQL

### 2.5 Iniciar el Despliegue

**Opción 1: Automático (Recomendado)**
- Railway detecta cambios en tu repositorio y redeploya automáticamente

**Opción 2: Manual por CLI**
```bash
railway up
```

### 2.6 Verificar que está funcionando
```bash
# Ver logs en tiempo real
railway logs

# Verificar estado del bot
railway status
```

## Paso 3: Configurar Webhook de Telegram (Opcional pero Recomendado)

Si quieres usar webhooks en lugar de polling (mejor para Railway):

```bash
# En tu máquina local, ejecuta:
curl -X POST \
  https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d "url=https://tu-proyecto-railway.up.railway.app/webhook" \
  -d "drop_pending_updates=True"
```

Reemplaza:
- `<TOKEN>`: Tu token de Telegram
- `tu-proyecto-railway.up.railway.app`: El dominio que Railway genera para tu bot

## Paso 4: Monitoreo y Mantenimiento

### Ver logs
```bash
railway logs -f  # Seguimiento en vivo
```

### Ver el estado de la base de datos
```bash
# Desde Railway CLI
railway logs (para ver errores de base de datos)
```

### Respaldar base de datos
```bash
# Railway proporciona backups automáticos
# Ve a PostgreSQL → Backups en el dashboard
```

## Estructura Final en Railway

```
🚂 Railway Project
├── 🐍 Bot (Python) - Tu bot de Telegram
│   ├── Variables: TOKEN, ADMIN_ID, GRUPO_RIFAS_ID
│   └── DATABASE_URL (auto-vinculado)
│
└── 🐘 PostgreSQL - Base de datos
    └── DATABASE_URL (auto-generada)
```

## Solución de Problemas

### "ModuleNotFoundError: No module named 'psycopg2'"
- Tu `requirements.txt` debe tener `psycopg2-binary==2.9.9`
- Railway instalará automáticamente desde requirements.txt

### "Lost connection to PostgreSQL"
- Verifica que `DATABASE_URL` esté configurada en Railway
- Comprueba en el servicio PostgreSQL que esté activo

### "Bot no responde"
- Verifica en los logs: `railway logs`
- Confirma que `TOKEN` esté correcto en las variables

### "telegram.error.BadRequest: Chat not found"
- Verifica que `ADMIN_ID` y `GRUPO_RIFAS_ID` sean correctos
- Asegúrate de que el bot sea miembro del grupo

## Comandos Útiles de Railway CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Ver logs
railway logs

# Mostrar variables
railway variables

# Ejecutar un comando remoto
railway run python migrate_to_postgresql.py

# Ver estado
railway status
```

## Resumen Final

1. ✅ Migra de SQLite a PostgreSQL
2. ✅ Configura variables en `.env`
3. ✅ Sube a GitHub
4. ✅ Conecta Railway a tu repositorio
5. ✅ Agrega PostgreSQL en Railway
6. ✅ Configura variables de entorno
7. ✅ ¡Tu bot está en vivo! 🎉

## Notas Importantes

- Railway reinicia el bot automáticamente cuando actualices el código
- PostgreSQL en Railway tiene un plan gratuito con buena capacidad
- Los logs se mantienen por 24 horas, descárgalos regularmente
- Railway puede requerir tarjeta de crédito (pero tiene tier gratuito)
