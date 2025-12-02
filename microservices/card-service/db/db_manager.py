# card-service/db/db_manager.py

import os
import logging
import time
from contextlib import contextmanager
from psycopg2 import pool, OperationalError, errorcodes
import psycopg2
from psycopg2.extras import RealDictCursor

# -----------------------
# Logging
# -----------------------

logger = logging.getLogger("card_service.db")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)


# -----------------------
# Database configuration
# -----------------------

DB_NAME = os.getenv("CARD_DB_NAME", "card_db")
DB_USER = os.getenv("DB_USER", "gameuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "gamepassword")
DB_HOST = os.getenv("DB_HOST", "postgresql")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# -----------------------
# Connection Pool
# -----------------------

connection_pool = None

def init_connection_pool():
    global connection_pool

    if connection_pool is not None:
        return connection_pool

    logger.info("Initializing card-service PostgreSQL connection pool...")

    for i in range(15):  # retry attempts
        try:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                cursor_factory=RealDictCursor,
            )
            logger.info("Connection pool initialized successfully.")
            return connection_pool

        except OperationalError as e:
            logger.warning(f"Database not ready yet (attempt {i+1}/15): {e}")
            time.sleep(2)

    raise RuntimeError("Failed to initialize database connection pool after retries.")


# -----------------------
# Ensuring card_db exists
# -----------------------

def ensure_card_db_exists():
    """
    Connects to default 'postgres' or 'battlecards' DB to create card_db if missing.
    """
    logger.info("Ensuring card_db exists...")

    try:
        conn = psycopg2.connect(
            dbname="battlecards",  # your default DB
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (DB_NAME,))
        exists = cur.fetchone()

        if not exists:
            logger.info("Creating card_db database...")
            cur.execute(f'CREATE DATABASE {DB_NAME};')
            logger.info("card_db created successfully!")

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Failed to ensure card_db exists: {e}")
        raise


# -----------------------
# Get Connection
# -----------------------

def get_connection():
    """
    Returns a pooled connection.
    """
    if connection_pool is None:
        init_connection_pool()

    return connection_pool.getconn()


def release_connection(conn):
    if connection_pool:
        connection_pool.putconn(conn)


# -----------------------
# Unit of Work (transaction manager)
# -----------------------

@contextmanager
def unit_of_work():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


# -----------------------
# Health Check
# -----------------------

def db_health():
    try:
        with unit_of_work() as cur:
            cur.execute("SELECT 1;")
            return {"database": "ok"}
    except:
        return {"database": "unavailable"}
