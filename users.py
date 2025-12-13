from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db

def login(username, password):
    sql = text('SELECT id, username, password FROM users WHERE username=:username')
    result = db.session.execute(sql, {'username': username})
    user = result.fetchone()

    if user and check_password_hash(user[2], password):
        return True

    return False


def register(username, password):
    sql = text('SELECT id FROM users WHERE username=:username')
    user = db.session.execute(sql, {'username': username}).fetchone()

    if user:
        return False

    hashed_password = generate_password_hash(password)

    sql = text('INSERT INTO users (username, password) VALUES (:username, :password)')
    db.session.execute(sql, {
        'username': username,
        'password': hashed_password
    })
    db.session.commit()

    return True


def delete_user(username):
    sql = text('DELETE FROM users WHERE username=:username')
    db.session.execute(sql, {'username': username})
    db.session.commit()
    return True
