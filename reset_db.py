"""
Script para resetear la base de datos (elimina tablas viejas y crea nuevas)
Úsalo solo si quieres empezar desde cero
"""
import os
import psycopg2
from urllib.parse import urlparse

def reset_db():
    """Elimina todas las tablas y las recrear con la estructura correcta"""
    
    database_url = os.getenv("DATABASE_URL") or "postgresql://postgres:password@localhost:5432/rifas_bot"
    parsed = urlparse(database_url)
    
    db_config = {
        "host": parsed.hostname,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path[1:],
        "port": parsed.port or 5432,
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    print("⚠️  Eliminando tablas antiguas...")
    
    try:
        # Eliminar en orden inverso de dependencias
        cursor.execute("DROP TABLE IF EXISTS pagos CASCADE")
        cursor.execute("DROP TABLE IF EXISTS numeros CASCADE")
        cursor.execute("DROP TABLE IF EXISTS usuarios CASCADE")
        cursor.execute("DROP TABLE IF EXISTS rifas CASCADE")
        
        conn.commit()
        print("✅ Tablas eliminadas")
        
        # Recrear con estructura correcta
        print("📝 Creando nuevas tablas...")
        
        cursor.execute("""
        CREATE TABLE rifas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            precio INTEGER NOT NULL,
            total_numeros INTEGER NOT NULL,
            activa INTEGER DEFAULT 1
        )
        """)
        
        cursor.execute("""
        CREATE TABLE numeros (
            id SERIAL PRIMARY KEY,
            rifa_id INTEGER REFERENCES rifas(id) ON DELETE CASCADE,
            numero INTEGER,
            user_id BIGINT,
            pago_id INTEGER,
            reservado INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("""
        CREATE TABLE usuarios (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            nombre TEXT,
            telefono TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE pagos (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            rifa_id INTEGER REFERENCES rifas(id) ON DELETE CASCADE,
            comprobante TEXT,
            estado TEXT,
            timestamp INTEGER
        )
        """)
        
        conn.commit()
        print("✅ Nuevas tablas creadas correctamente")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset_db()
    print("\n✅ ¡Base de datos reseteada correctamente!")
