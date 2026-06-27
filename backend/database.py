"""
Database connection management for Project Shikhara.
Uses a connection pool for efficient reuse of PostgreSQL connections.
"""

import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Connection pool ───────────────────────────────────────────────────────────
# minconn=1: always keep at least 1 connection open
# maxconn=10: never open more than 10 simultaneous connections

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)


def get_connection():
    """Borrow a connection from the pool."""
    return connection_pool.getconn()


def release_connection(conn):
    """Return a connection back to the pool."""
    connection_pool.putconn(conn)


def get_db():
    """
    FastAPI dependency — yields a database connection for the duration
    of a request, then returns it to the pool automatically.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        release_connection(conn)