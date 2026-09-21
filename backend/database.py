"""
Database layer with two backends behind one tiny interface:

  * DATABASE_URL set  -> PostgreSQL (e.g. a free Neon database). Required on Vercel,
                         because serverless functions have no persistent disk.
  * DATABASE_URL empty -> local SQLite file (backend/app.db). Zero setup for local dev.

Callers just do:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM pantry WHERE user_id = ?", (uid,)).fetchall()
        conn.commit()
Queries are written with `?` placeholders; they're translated for Postgres automatically.
Rows support row["column"] and dict(row) on both backends.

Tables: users, sessions, pantry, cook_history, favorites, nutrition_cache.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))
ON_VERCEL = bool(os.environ.get("VERCEL"))

DB_PATH = Path(__file__).parent / "app.db"

_schema_ready = False


def backend_name() -> str:
    if USE_PG:
        return "postgres"
    if ON_VERCEL:
        return "missing"  # on Vercel there's no disk, so SQLite can't work
    return "sqlite"


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS pantry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity TEXT DEFAULT '',
    added_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);
CREATE TABLE IF NOT EXISTS cook_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipe_id TEXT NOT NULL,
    recipe_name TEXT NOT NULL,
    cooked_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipe_id TEXT NOT NULL,
    UNIQUE(user_id, recipe_id)
);
CREATE TABLE IF NOT EXISTS nutrition_cache (
    recipe_id TEXT PRIMARY KEY,
    calories REAL,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL
);
"""

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pantry (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity TEXT DEFAULT '',
    added_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, name)
);
CREATE TABLE IF NOT EXISTS cook_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    recipe_id TEXT NOT NULL,
    recipe_name TEXT NOT NULL,
    cooked_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    recipe_id TEXT NOT NULL,
    UNIQUE(user_id, recipe_id)
);
CREATE TABLE IF NOT EXISTS nutrition_cache (
    recipe_id TEXT PRIMARY KEY,
    calories DOUBLE PRECISION,
    protein_g DOUBLE PRECISION,
    carbs_g DOUBLE PRECISION,
    fat_g DOUBLE PRECISION
);
"""


# ------------------------------------------------------------------
# Connections
# ------------------------------------------------------------------
class _PgConn:
    """Thin wrapper so the rest of the app can keep using `?` placeholders."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=()):
        return self._conn.execute(sql.replace("?", "%s"), params)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def _open_pg() -> _PgConn:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=10,
        # Neon's pooled endpoint (PgBouncer) is happiest without server-side prepared statements
        prepare_threshold=None,
    )
    return _PgConn(conn)


def _open_sqlite():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn):
    """Create tables once per process (cheap no-op if they already exist)."""
    global _schema_ready
    if _schema_ready:
        return
    try:
        if USE_PG:
            conn.execute(PG_SCHEMA)  # several statements in one round trip (no parameters)
            conn.commit()
        else:
            conn.executescript(SQLITE_SCHEMA)
            conn.commit()
    except Exception:
        # Two cold starts can race on CREATE TABLE; if the tables exist we're fine.
        if USE_PG:
            try:
                conn._conn.rollback()
            except Exception:
                pass
        else:
            raise
    _schema_ready = True


def init_db():
    """Optional: create tables now (they're also created lazily on first use)."""
    with get_conn():
        pass


@contextmanager
def get_conn():
    if not USE_PG and ON_VERCEL:
        raise RuntimeError(
            "DATABASE_URL is not set. On Vercel, add a Postgres connection string "
            "(e.g. from a free Neon database) in Project Settings -> Environment Variables."
        )
    conn = _open_pg() if USE_PG else _open_sqlite()
    try:
        _ensure_schema(conn)
        yield conn
    finally:
        conn.close()


def ping() -> str:
    """For /api/health: 'ok' or a short reason the database can't be reached."""
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:120]}"
