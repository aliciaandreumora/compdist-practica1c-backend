from os import getenv
from dotenv import load_dotenv
from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, set_access_cookies,
    unset_jwt_cookies, jwt_required, get_jwt_identity
)
from sqlalchemy import text

from extensions import db  # extensions.py debe tener: db = SQLAlchemy()

import users
import games


def create_app():
    load_dotenv()

    app = Flask(__name__, static_url_path="/static")

    # Secret keys (ponlas en Render en Environment Variables)
    app.config["SECRET_KEY"] = getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    # DB url (Render usa DATABASE_URL)
    db_url = getenv("DATABASE_URL") or getenv("SQLALCHEMY_DATABASE_URI")
    if not db_url:
        # fallback local (SQLite)
        db_url = "sqlite:///games.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # JWT cookies (GitHub Pages -> Render: cross-site)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = True          # Render es HTTPS
    app.config["JWT_COOKIE_SAMESITE"] = "None"      # permitir cross-site cookies
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    # CORS
    # Puedes controlar orígenes con env var FRONTEND_ORIGINS (comma-separated)
    origins_env = getenv("FRONTEND_ORIGINS", "").strip()
    default_origins = [
        "https://aliciaandreumora.github.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    origins = [o.strip() for o in origins_env.split(",") if o.strip()] or default_origins

    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )

    JWTManager(app)

    # ✅ CREAR TABLAS (porque NO usas modelos SQLAlchemy)
    with app.app_context():
        init_db_tables()

    return app


def init_db_tables():
    """Crea tablas users y games si no existen (Postgres o SQLite)."""
    dialect = db.engine.dialect.name  # 'postgresql' o 'sqlite' etc.

    if dialect == "sqlite":
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        """
        games_sql = """
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            year INTEGER,
            description TEXT,
            img TEXT,
            url TEXT,
            play TEXT
        );
        """
    else:
        # PostgreSQL (Render)
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        """
        games_sql = """
        CREATE TABLE IF NOT EXISTS games (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            year INTEGER,
            description TEXT,
            img TEXT,
            url TEXT,
            play TEXT
        );
        """

    db.session.execute(text(users_sql))
    db.session.execute(text(games_sql))
    db.session.commit()


app = create_app()


@app.get("/")
def index():
    return jsonify({"msg": "API OK"}), 200


@app.route("/login", methods=["POST", "OPTIONS"])
def login_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user_ok = users.login(username, password)

    if user_ok:
        access_token = create_access_token(identity=username)
        response = jsonify({"msg": "logged in"})
        set_access_cookies(response, access_token)
        return response

    return jsonify({"msg": "Bad username or password"}), 401


@app.route("/logout", methods=["POST", "OPTIONS"])
def logout_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    resp = jsonify({"msg": "logout ok"})
    unset_jwt_cookies(resp)
    return resp


@app.route("/register", methods=["POST", "OPTIONS"])
def register_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    register_ok = users.register(username, password)
    if register_ok:
        access_token = create_access_token(identity=username)
        response = jsonify({"msg": f"User {username} registered and logged in"})
        set_access_cookies(response, access_token)
        return response

    return jsonify({"msg": "Registration not successful"}), 409


@app.route("/delete_user", methods=["POST", "OPTIONS"])
@jwt_required(optional=False)
def delete_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    username = get_jwt_identity()
    deletion_ok = users.delete_user(username)

    if deletion_ok:
        response = jsonify({"msg": f"User {username} deleted"})
        unset_jwt_cookies(response)
        return response, 200

    return jsonify({"msg": f"Deletion of user {username} not successful"}), 400


@app.route("/me", methods=["GET", "OPTIONS"])
@jwt_required(optional=False)
def me():
    if request.method == "OPTIONS":
        return make_response("", 204)
    return jsonify({"user": get_jwt_identity()}), 200


@app.route("/api/juegos", methods=["GET", "OPTIONS"])
@jwt_required(optional=False)
def listar_juegos():
    if request.method == "OPTIONS":
        return make_response("", 204)
    ret, codigo = games.listar_juegos()
    return ret, codigo


@app.route("/api/juegos", methods=["POST", "OPTIONS"])
@jwt_required(optional=False)
def crear_juego():
    if request.method == "OPTIONS":
        return make_response("", 204)

    ret, codigo = games.crear_juego(request)
    return ret, codigo


@app.route("/api/juegos/<int:id>", methods=["PUT", "OPTIONS"])
@jwt_required(optional=False)
def editar_juego(id):
    if request.method == "OPTIONS":
        return make_response("", 204)
    ret, codigo = games.editar_juego(id, request)
    return ret, codigo


@app.route("/api/juegos/<int:id>", methods=["DELETE", "OPTIONS"])
@jwt_required(optional=False)
def eliminar_juego(id):
    if request.method == "OPTIONS":
        return make_response("", 204)
    ret, codigo = games.eliminar_juego(id)
    return ret, codigo


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
