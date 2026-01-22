import psycopg2
from psycopg2 import pool
import os
from urllib.parse import urlparse

# Pool de conexiones PostgreSQL
connection_pool = None

def init_connection_pool():
    global connection_pool
    
    # Leer la URL de la base de datos (Railway proporciona DATABASE_URL)
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Fallback para desarrollo local
        database_url = "postgresql://postgres:password@localhost:5432/rifas_bot"
    
    # Parsear la URL
    parsed = urlparse(database_url)
    
    db_config = {
        "host": parsed.hostname,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path[1:],  # Remover el '/'
        "port": parsed.port or 5432,
    }
    
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 5, **db_config
    )

def get_db():
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.getconn()

def return_db(conn):
    if connection_pool:
        connection_pool.putconn(conn)

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    try:
        # RIFAS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rifas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            precio INTEGER NOT NULL,
            total_numeros INTEGER NOT NULL,
            activa INTEGER DEFAULT 1
        )
        """)

        # NUMEROS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS numeros (
            id SERIAL PRIMARY KEY,
            rifa_id INTEGER REFERENCES rifas(id) ON DELETE CASCADE,
            numero INTEGER,
            user_id INTEGER,
            pago_id INTEGER,
            reservado INTEGER DEFAULT 0
        )
        """)

        # USUARIOS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            nombre TEXT,
            telefono TEXT
        )
        """)

        # PAGOS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            rifa_id INTEGER REFERENCES rifas(id) ON DELETE CASCADE,
            comprobante TEXT,
            estado TEXT,
            timestamp INTEGER
        )
        """)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db(conn)
