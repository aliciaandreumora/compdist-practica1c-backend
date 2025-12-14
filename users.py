from sqlalchemy import text
from extensions import db


def login(username, password) -> bool:
    sql = text("SELECT id, username, password FROM users WHERE username=:username")
    row = db.session.execute(sql, {"username": username}).fetchone()
    if not row:
        return False
    return row[2] == password


def register(username, password):
    sql = text("SELECT id FROM users WHERE username=:username")
    row = db.session.execute(sql, {"username": username}).fetchone()
    if row:
        return False, "Username already exists"

    ins = text("INSERT INTO users (username, password) VALUES (:username, :password)")
    db.session.execute(ins, {"username": username, "password": password})
    db.session.commit()
    return True, "ok"


def delete_user(username) -> bool:
    sql = text("SELECT id FROM users WHERE username=:username")
    row = db.session.execute(sql, {"username": username}).fetchone()
    if not row:
        return False

    del_sql = text("DELETE FROM users WHERE username=:username")
    db.session.execute(del_sql, {"username": username})
    db.session.commit()
    return True

