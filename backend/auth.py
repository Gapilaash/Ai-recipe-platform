"""
Lightweight self-hosted auth: username/password with salted PBKDF2 hashes
and random session tokens stored in SQLite. No external auth service, no
cost, no third-party dependency (uses only Python's built-in hashlib/secrets).
"""
import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import Cookie, HTTPException

from database import get_conn

SESSION_DAYS = 30


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


def create_user(username: str, password: str) -> int:
    username = username.strip().lower()
    if len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise HTTPException(409, "That username is already taken")
        row = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?) RETURNING id",
            (username, hash_password(password)),
        ).fetchone()
        conn.commit()
        return row["id"]


def authenticate(username: str, password: str) -> int:
    username = username.strip().lower()
    with get_conn() as conn:
        row = conn.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,)).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            raise HTTPException(401, "Invalid username or password")
        return row["id"]


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires),
        )
        conn.commit()
    return token


def destroy_session(token: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


def get_current_user(session_token: str | None = Cookie(default=None)) -> dict:
    """FastAPI dependency: returns {'id':.., 'username':..} or raises 401."""
    if not session_token:
        raise HTTPException(401, "Not logged in")
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, s.expires_at FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (session_token,),
        ).fetchone()
    if not row:
        raise HTTPException(401, "Session expired, please log in again")
    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        destroy_session(session_token)
        raise HTTPException(401, "Session expired, please log in again")
    return {"id": row["id"], "username": row["username"]}


def get_current_user_optional(session_token: str | None = Cookie(default=None)) -> dict | None:
    """Same as above but returns None instead of raising, for optional-auth endpoints."""
    try:
        return get_current_user(session_token)
    except HTTPException:
        return None
