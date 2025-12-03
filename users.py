from flask import session, abort
from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from extensions import db

print("DB instance in users.py:", id(db))

def login(username, password):

    sql = text('SELECT id, username, password FROM users WHERE username=:username')
    result = db.session.execute(sql, {'username': username})
    user = result.fetchone()

    if user and check_password_hash(user[2], password):
        print("HEP!")
        session['user_id'] = user[0]
        session['username'] = user[1]
        token = get_token()
        session['csrf_token'] = token
        #return token, 200
        return True

    #return "EI", 200
    return False

def logout():
    if 'user_id' in session:
        del session['user_id']
    if 'username' in session:
        del session['username']
    if 'csrf_token' in session:
        del session['csrf_token']
    return True


def register(username, password):

    sql = text('SELECT id, username FROM users WHERE username=:username')
    result = db.session.execute(sql, {'username': username})
    user = result.fetchone()

    if user:
        return False

    hashed_password = generate_password_hash(password)

    sql = text('INSERT INTO users (username, password) VALUES (:username, :password)')
    db.session.execute(sql, {'username': username, 'password': hashed_password})
    db.session.commit()

    return True


def delete_user(username):
    sql = text('SELECT id, username FROM users WHERE username=:username')
    result = db.session.execute(sql, {'username': username})
    user = result.fetchone()

    if user:
        sql = text('DELETE FROM users WHERE username=:username')
        db.session.execute(sql, {'username': username})
        return True

    return False


def get_token(num=12):
    token = secrets.token_hex(num)
    return token


def check_csrf_token(token):
    if token == session['csrf_token']:
        return True
    else:
        return False
