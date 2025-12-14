from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from extensions import db

def register(username: str, password: str) -> bool:
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return False

    exists = db.session.execute(
        text("SELECT id FROM users WHERE username=:u"),
        {"u": username}
    ).fetchone()

    if exists:
        return False

    pwd_hash = generate_password_hash(password)
    db.session.execute(
        text("INSERT INTO users (username, password) VALUES (:u, :p)"),
        {"u": username, "p": pwd_hash}
    )
    db.session.commit()
    return True


def login(username: str, password: str) -> bool:
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return False

    row = db.session.execute(
        text("SELECT password FROM users WHERE username=:u"),
        {"u": username}
    ).fetchone()

    if not row:
        return False

    return check_password_hash(row[0], password)


def delete_user(username: str) -> bool:
    username = (username or "").strip()
    if not username:
        return False

    db.session.execute(
        text("DELETE FROM users WHERE username=:u"),
        {"u": username}
    )
    db.session.commit()
    return True
