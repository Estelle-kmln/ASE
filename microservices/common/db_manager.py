import os
import time
import logging
from contextlib import contextmanager
from psycopg2 import pool, OperationalError
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("common.db_manager")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Read DATABASE_URL from env (the docker-compose already sets DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gameuser:gamepassword@postgresql:5432/battlecards")

# Pool parameters
_MIN_CONN = int(os.getenv("DB_POOL_MIN", "1"))
_MAX_CONN = int(os.getenv("DB_POOL_MAX", "10"))

_pool = None

def _init_pool():
    global _pool
    if _pool:
        return _pool

    # Retry loop: wait for Postgres to be ready (useful during container startup)
    for attempt in range(15):
        try:
            # psycopg2 can accept a DSN string
            _pool = pool.SimpleConnectionPool(
                minconn=_MIN_CONN,
                maxconn=_MAX_CONN,
                dsn=DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            logger.info("Postgres connection pool created.")
            return _pool
        except OperationalError as e:
            logger.warning(f"Postgres not ready (attempt {attempt+1}/15): {e}")
            time.sleep(2)
    raise RuntimeError("Unable to create Postgres connection pool after retries.")

def get_connection():
    """
    Get a raw connection from the pool. Caller MUST call release_connection(conn).
    Use this when a function needs the connection object (e.g., to pass into archive_game_history).
    """
    if _pool is None:
        _init_pool()
    return _pool.getconn()

def release_connection(conn):
    """Release a raw connection back to the pool."""
    if _pool and conn:
        try:
            _pool.putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

@contextmanager
def unit_of_work():
    """
    Context manager yielding a cursor with automatic commit/rollback.
    Usage:
        with unit_of_work() as cur:
            cur.execute(...)
            rows = cur.fetchall()
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        yield cur
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        release_connection(conn)

def db_health():
    """Return a dict describing DB health - suitable for incorporating into service /health."""
    try:
        with unit_of_work() as cur:
            cur.execute("SELECT 1")
            _ = cur.fetchone()
        return {"database": "ok"}
    except Exception as e:
        logger.exception("DB health check failed")
        return {"database": "unavailable", "error": str(e)}
