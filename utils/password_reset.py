import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from flask import current_app, request
from db import get_database

def _sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def create_reset_token(user_id: int) -> str:
    ttl = int(current_app.config.get("PASSWORD_RESET_TOKEN_TTL_MIN", 30))
    token = secrets.token_urlsafe(32)
    token_hash = _sha(token)
    expires = (datetime.utcnow() + timedelta(minutes=ttl).strftime("%Y-%m-%d %H:%M:%S"))
    db = get_database()
    db.execute("""INSERT INTO password_reset_tokens
                  (user_id, token_hash, expires_at, request_ip, request_ua)
                  VALUES (?,?,?,?,?)""",
               (user_id, token_hash, expires, request.remote_addr, request.header.get("User-Agent", "")[:255]))
    db.commit()
    return token

def load_valid_token(token: str) -> Optional[Dict]:
    token_hash = _sha(token)
    db = get_database()
    row = db.execute("""SELECT id, user_id, expires_at, used_at
                        FROM password_reset_tokens WHERE token_hash=?""",
                     (token_hash,)).fetchone()
    if not row or row["used_at"] is not None:
        return None
    if datetime.utcnow() > datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S"):
        return None
    return dict(row)

def burn(token: str) -> None:
    token_hash = _sha(token)
    db = get_database()
    db.execute("UPDATE password_reset_tokens SET used_at=datetime('now') WHERE token_hash=?", (token_hash,))
    db.commit()


