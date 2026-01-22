# 📋 GUÍA PASO A PASO: DE SQLite A PostgreSQL EN RAILWAY

## ⏱️ Tiempo estimado: 30-45 minutos

---

## PARTE 1: PREPARAR TU MÁQUINA (10 minutos)

### Paso 1.1: Instalar PostgreSQL

**Windows:**
1. Descarga: https://www.postgresql.org/download/windows/
2. Instala (anota la contraseña)
3. Abre pgAdmin para verificar

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Paso 1.2: Crear Base de Datos Local

```bash
psql -U postgres
CREATE DATABASE rifas_bot;
\q
```

### Paso 1.3: Configurar `.env`

Edita el archivo `.env`:

```
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/rifas_bot
TOKEN=tu_token_aqui
ADMIN_ID=tu_id_aqui
GRUPO_RIFAS_ID=id_del_grupo_aqui
```

**¿Dónde obtener TOKEN, ADMIN_ID, GRUPO_RIFAS_ID?**

- **TOKEN**: Habla con [@BotFather](https://t.me/botfather) → `/newbot`
- **ADMIN_ID**: Habla con [@userinfobot](https://t.me/userinfobot)
- **GRUPO_RIFAS_ID**: Envía un mensaje al grupo, abre:
  ```
  https://api.telegram.org/bot<TOKEN>/getUpdates
  ```
  Busca `"chat":{"id":-1001234...`

### Paso 1.4: Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

## PARTE 2: MIGRAR DATOS (5 minutos)

### Paso 2.1: Si tienes datos en SQLite

```bash
python migrate_to_postgresql.py
```

Verás:
```
📊 Iniciando migración de SQLite a PostgreSQL...
📥 Migrando rifas...
✅ 2 rifas migradas
📥 Migrando usuarios...
✅ 5 usuarios migrados
...
✅ ¡Migración completada exitosamente!
```

### Paso 2.2: Si es nuevo (sin datos previos)

Salta al Paso 3. El bot creará las tablas automáticamente.

---

## PARTE 3: PROBAR LOCALMENTE (10 minutos)

### Paso 3.1: Ejecutar el Bot

```bash
python bot.py
```

Deberías ver:
```
🤖 Bot corriendo...
```

### Paso 3.2: Probar en Telegram

1. Abre Telegram
2. Busca tu bot (el que creaste con @BotFather)
3. Escribe `/start`
4. El bot debería responder

✅ Si funciona, ¡tu bot local está listo!

---

## PARTE 4: PREPARAR PARA RAILWAY (5 minutos)

### Paso 4.1: Crear Repositorio en GitHub

1. Ve a https://github.com
2. New Repository
3. Nombre: `telegram-rifas-bot`
4. Descripción: "Bot de rifas en Telegram"
5. Create repository

### Paso 4.2: Subir tu código a GitHub

```bash
cd telegram-rifas-bot
git init
git add .
git commit -m "Bot inicial migrado a PostgreSQL"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/telegram-rifas-bot.git
git push -u origin main
```

> ℹ️ Reemplaza `TU_USUARIO` con tu usuario de GitHub

### Paso 4.3: Crear Archivo `.gitignore`

Ya existe en tu proyecto (cubre archivos sensibles)

---

## PARTE 5: DESPLEGAR EN RAILWAY (15 minutos)

### Paso 5.1: Crear Cuenta en Railway

1. Ve a https://railway.app
2. "Start Building Now"
3. "Continue with GitHub"
4. Autoriza Railway

### Paso 5.2: Crear Proyecto

1. "New Project"
2. "Deploy from GitHub repo"
3. Autoriza si pide
4. Selecciona `telegram-rifas-bot`

### Paso 5.3: Agregar PostgreSQL

En tu proyecto:
1. "Add Service"
2. "Add from marketplace"
3. Busca **PostgreSQL** → Click
4. Listo, Railway crea automáticamente `DATABASE_URL`

**Espera 1 minuto** a que PostgreSQL inicie (verás "Running" en verde)

### Paso 5.4: Configurar Variables

1. Selecciona tu servicio del bot (el que dice "Python")
2. Tab "Variables"
3. Agrega:
   - `TOKEN` = tu_token
   - `ADMIN_ID` = tu_id
   - `GRUPO_RIFAS_ID` = id_del_grupo

❌ NO agregues `DATABASE_URL` (se agrega automáticamente)

### Paso 5.5: Primera Ejecución

El bot debería desplegarse automáticamente:
1. Ve a Logs
2. Deberías ver "🤖 Bot corriendo..."

✅ ¡Tu bot está vivo!

### Paso 5.6: Probar en Telegram

1. Abre Telegram
2. Escribe `/start` a tu bot
3. Si responde, ¡funciona perfectamente!

---

## PARTE 6: ACTUALIZAR EL BOT (Futuro)

Cada vez que quieras actualizar:

```bash
# Hacer cambios en bot.py
nano bot.py

# Guardar y subir a GitHub
git add .
git commit -m "Cambios: descripción"
git push origin main
```

🚀 Railway redeploya automáticamente (en 1-2 minutos)

---

## ✅ CHECKLIST FINAL

- [ ] PostgreSQL instalado localmente
- [ ] `.env` configurado
- [ ] Datos migrados (si tenías SQLite)
- [ ] Bot funciona localmente (`python bot.py`)
- [ ] Código subido a GitHub
- [ ] Repositorio conectado a Railway
- [ ] PostgreSQL agregado a Railway
- [ ] Variables configuradas en Railway
- [ ] Bot desplegado en Railway
- [ ] `/start` funciona en Telegram

---

## 🆘 SI ALGO FALLA

### "Bot no responde en Telegram"

```bash
# Verifica logs en Railway
# O localmente:
python bot.py
# Busca mensajes de error
```

**Causas comunes:**
- TOKEN incorrecto → Actualiza en [@BotFather](https://t.me/botfather)
- DATABASE_URL no configurada → Revisa que PostgreSQL esté agregado
- Error de conexión → Revisa los logs

### "DATABASE CONNECTION REFUSED"

1. Abre Railway
2. Ve al servicio PostgreSQL
3. Verifica que esté "Running" (verde)
4. Si no, click "Restart Service"

### "ModuleNotFoundError: No module named 'psycopg2'"

Asegúrate que `requirements.txt` tenga `psycopg2-binary`:

```bash
pip install -r requirements.txt
```

---

## 📚 DOCUMENTACIÓN COMPLETA

Para información más detallada:
- **Despliegue:** Ver [RAILWAY_GUIA_COMPLETA.md](RAILWAY_GUIA_COMPLETA.md)
- **Migraciones:** Ver [migrate_to_postgresql.py](migrate_to_postgresql.py)
- **Código:** Ver [bot.py](bot.py) y [database.py](database.py)

---

## 🎉 ¡LISTO!

Tu bot de rifas ahora está:
✅ Migrado a PostgreSQL
✅ Desplegado en Railway
✅ Corriendo 24/7
✅ Listo para producción

**Próximos pasos:**
1. Agrega usuarios a tu grupo de Telegram
2. Crea rifas con `/crearrifa`
3. ¡Gestiona tus rifas sin problemas!

---

## 💡 COMANDOS ÚTILES

```bash
# Ver logs en tiempo real
railway logs -f

# Reiniciar el bot
railway up

# Ver variables
railway variables

# Ejecutar un comando remoto
railway run python migrate_to_postgresql.py
```

---

**¡Mucho éxito! 🚀**

Si tienes dudas, revisa las guías o los logs de Railway.
