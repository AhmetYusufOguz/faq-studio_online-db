import os, psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector
from app.config import settings

def get_conn():
    conn = psycopg.connect(settings.DATABASE_URL, row_factory=dict_row)
    # Register pgvector adapter so we can pass Vector() objects
    register_vector(conn)
    return conn


def init_db():
    from os.path import dirname, join
    path = join(dirname(__file__), "schema.sql")
    
    # İlk olarak vector extension olmadan bağlan
    conn = psycopg.connect(settings.DATABASE_URL, row_factory=dict_row)
    
    try:
        with conn.cursor() as cur, open(path, "r", encoding="utf-8") as f:
            sql = f.read()
            # Remove UTF-8 BOM if present
            if sql.startswith("\ufeff"):
                sql = sql.lstrip("\ufeff")
            # Execute the entire SQL as one statement instead of splitting by semicolon
            # This prevents breaking DO $ blocks
            cur.execute(sql)
            conn.commit()
    finally:
        conn.close()
    
    # Şimdi vector extension yüklendiği için normal get_conn() kullanabiliriz
    # Test bağlantısı yap
    with get_conn() as test_conn:
        pass