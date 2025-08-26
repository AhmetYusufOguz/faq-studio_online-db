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
    with get_conn() as conn, conn.cursor() as cur, open(path, "r", encoding="utf-8") as f:
        sql = f.read()
        # Remove UTF-8 BOM if present
        if sql.startswith("\ufeff"):
            sql = sql.lstrip("\ufeff")
        # Execute statements one by one
        for stmt in sql.split(";"):
            if stmt.strip():
                cur.execute(stmt)
        conn.commit()
