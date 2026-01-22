# 🎟️ Bot de Rifas en Telegram

Bot de Telegram para gestionar rifas con integración de pagos, almacenamiento en PostgreSQL y despliegue en Railway.

## ✨ Características

- ✅ Registro de usuarios
- 🎟️ Selección de números de rifa
- 💳 Sistema de pagos con comprobante
- 📊 Estadísticas y talonario
- 👨‍💼 Panel de admin
- 📱 Interfaz intuitiva con botones inline
- 🐘 Base de datos PostgreSQL
- 🚀 Listo para desplegar en Railway

## 🗂️ Estructura del Proyecto

```
telegram-rifas-bot/
├── bot.py                      # Bot principal (Telegram)
├── database.py                 # Gestión de base de datos PostgreSQL
├── migrate_to_postgresql.py    # Script para migrar datos de SQLite
├── requirements.txt            # Dependencias Python
├── Dockerfile                  # Imagen Docker para Railway
├── railway.json               # Configuración para Railway
├── .env.example               # Plantilla de variables de entorno
├── .gitignore                 # Archivos a ignorar en Git
├── DEPLOYMENT_GUIDE.md        # Guía detallada de despliegue
└── README.md                  # Este archivo
```

## 📋 Requisitos

- Python 3.11+
- PostgreSQL 12+
- Cuenta de Telegram
- Cuenta en Railway
- Token de bot de Telegram

## 🚀 Inicio Rápido (Local)

### 1. Clonar o descargar el proyecto

```bash
git clone <tu-repositorio>
cd telegram-rifas-bot
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL

**Windows/macOS (con PostgreSQL instalado):**
```bash
psql -U postgres
CREATE DATABASE rifas_bot;
\q
```

**Con Docker:**
```bash
docker run --name postgres-rifas -e POSTGRES_PASSWORD=password -d postgres:15
```

### 4. Crear archivo `.env`

```bash
copy .env.example .env
```

Edita `.env` con tus valores:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/rifas_bot
TOKEN=tu_token_aqui
ADMIN_ID=tu_id_de_telegram
GRUPO_RIFAS_ID=id_del_grupo_aqui
```

### 5. Ejecutar el bot

```bash
python bot.py
```

Si tienes datos en SQLite anterior:
```bash
python migrate_to_postgresql.py
python bot.py
```

## 🌐 Despliegue en Railway

Ver la guía completa: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Resumen Rápido:

1. **Crear cuenta en Railway**: https://railway.app
2. **Conectar GitHub**: Autorizar Railway a tu repositorio
3. **Agregar PostgreSQL**: Railway → Add Service → PostgreSQL
4. **Configurar variables**:
   - `TOKEN`: Tu token de Telegram
   - `ADMIN_ID`: Tu ID de Telegram
   - `GRUPO_RIFAS_ID`: ID del grupo
   - `DATABASE_URL`: Se agrega automáticamente

5. **Deploy automático**: Railway despliega al hacer push a GitHub

## 📝 Comandos del Bot

### Para Usuarios

- `/start` - Comenzar y registrarse
- `/misboletas` - Ver tus compras aprobadas

### Para Admin

- `/crearrifa` - Crear una nueva rifa
- `/estadisticas <id_rifa>` - Ver estadísticas de una rifa
- `/talonario` - Ver talonario de ventas
- `/admin` - Panel de administración
- `/eliminar_rifa <id_rifa>` - Eliminar una rifa

## 🔄 Flujo del Bot

1. Usuario escribe `/start`
2. Se registra (nombre, teléfono)
3. Elige una rifa de las disponibles
4. Selecciona números (0-99)
5. Confirma la compra
6. Envía comprobante de pago (foto)
7. Admin revisa y aprueba/rechaza
8. Usuario recibe confirmación

## 🗄️ Estructura de Base de Datos

### Tabla: rifas
```
id: INTEGER PRIMARY KEY
nombre: TEXT
precio: INTEGER
total_numeros: INTEGER
activa: INTEGER (0/1)
```

### Tabla: numeros
```
id: INTEGER PRIMARY KEY
rifa_id: INTEGER (FK)
numero: INTEGER
user_id: INTEGER
pago_id: INTEGER (FK)
reservado: INTEGER (0/1)
```

### Tabla: usuarios
```
user_id: INTEGER PRIMARY KEY
username: TEXT
nombre: TEXT
telefono: TEXT
```

### Tabla: pagos
```
id: INTEGER PRIMARY KEY
user_id: INTEGER
rifa_id: INTEGER (FK)
comprobante: TEXT (file_id)
estado: TEXT ('pendiente', 'en_revision', 'aprobado', 'rechazado', 'expirado')
timestamp: INTEGER
```

## 🔐 Variables de Entorno

- `TOKEN` - Token del bot de Telegram (requerido)
- `ADMIN_ID` - ID de Telegram del administrador (requerido)
- `GRUPO_RIFAS_ID` - ID del grupo de Telegram (requerido)
- `DATABASE_URL` - URL de conexión a PostgreSQL (auto en Railway)

## 🐛 Solución de Problemas

### El bot no responde
```bash
# Verifica los logs
railway logs
# O localmente
python bot.py
```

### Error de conexión a base de datos
- Verifica que PostgreSQL esté corriendo
- Confirma las credenciales en `DATABASE_URL`
- En Railway, revisa que el servicio PostgreSQL esté activo

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Token inválido
- Obtén un nuevo token en [@BotFather](https://t.me/botfather)
- Actualiza la variable `TOKEN`

## 📚 Documentación Completa

Para guía paso a paso de despliegue con screenshots:
📖 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

## 🛠️ Migración de SQLite a PostgreSQL

Si tenías datos en SQLite:

```bash
python migrate_to_postgresql.py
```

⚠️ Asegúrate de que:
- Tu archivo `rifas.db` esté en el directorio
- `DATABASE_URL` esté configurada correctamente
- PostgreSQL esté corriendo

## 📞 Soporte

Para problemas o dudas, revisa:
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Solución de problemas
2. [Documentación de python-telegram-bot](https://docs.python-telegram-bot.org/)
3. [Documentación de psycopg2](https://www.psycopg.org/documentation/)

## 📄 Licencia

Este proyecto es de código abierto. Úsalo libremente.

---

**Hecho con ❤️ para gestionar rifas en Telegram**
