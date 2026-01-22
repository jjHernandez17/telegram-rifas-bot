"""
Script para migrar datos de SQLite a PostgreSQL
"""
import sqlite3
import psycopg2
from urllib.parse import urlparse
import os

def migrate_sqlite_to_postgresql():
    """Migra datos de SQLite a PostgreSQL"""
    
    # Conectar a SQLite
    sqlite_conn = sqlite3.connect("rifas.db")
    sqlite_cursor = sqlite_conn.cursor()
    
    # Conectar a PostgreSQL
    database_url = os.getenv("DATABASE_URL") or "postgresql://postgres:password@localhost:5432/rifas_bot"
    parsed = urlparse(database_url)
    
    pg_config = {
        "host": parsed.hostname,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path[1:],
        "port": parsed.port or 5432,
    }
    
    pg_conn = psycopg2.connect(**pg_config)
    pg_cursor = pg_conn.cursor()
    
    print("📊 Iniciando migración de SQLite a PostgreSQL...")
    
    try:
        # 1. Migrar RIFAS
        print("📥 Migrando rifas...")
        sqlite_cursor.execute("SELECT * FROM rifas")
        rifas = sqlite_cursor.fetchall()
        
        for rifa in rifas:
            pg_cursor.execute("""
                INSERT INTO rifas (id, nombre, precio, total_numeros, activa)
                VALUES (%s, %s, %s, %s, %s)
            """, rifa)
        
        pg_conn.commit()
        print(f"✅ {len(rifas)} rifas migradas")
        
        # 2. Migrar USUARIOS
        print("📥 Migrando usuarios...")
        sqlite_cursor.execute("SELECT * FROM usuarios")
        usuarios = sqlite_cursor.fetchall()
        
        for usuario in usuarios:
            pg_cursor.execute("""
                INSERT INTO usuarios (user_id, username, nombre, telefono)
                VALUES (%s, %s, %s, %s)
            """, usuario)
        
        pg_conn.commit()
        print(f"✅ {len(usuarios)} usuarios migrados")
        
        # 3. Migrar PAGOS
        print("📥 Migrando pagos...")
        sqlite_cursor.execute("SELECT * FROM pagos")
        pagos = sqlite_cursor.fetchall()
        
        for pago in pagos:
            pg_cursor.execute("""
                INSERT INTO pagos (id, user_id, rifa_id, comprobante, estado, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, pago)
        
        pg_conn.commit()
        print(f"✅ {len(pagos)} pagos migrados")
        
        # 4. Migrar NUMEROS
        print("📥 Migrando números...")
        sqlite_cursor.execute("SELECT * FROM numeros")
        numeros = sqlite_cursor.fetchall()
        
        for numero in numeros:
            pg_cursor.execute("""
                INSERT INTO numeros (id, rifa_id, numero, user_id, pago_id, reservado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, numero)
        
        pg_conn.commit()
        print(f"✅ {len(numeros)} números migrados")
        
        print("✅ ¡Migración completada exitosamente!")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Error durante la migración: {e}")
        raise
    
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_sqlite_to_postgresql()
