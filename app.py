from os import getenv
from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, set_access_cookies,
    unset_jwt_cookies, jwt_required, get_jwt_identity
)
from sqlalchemy import text
from datetime import timedelta
from extensions import db


def normalize_db_url(url: str | None) -> str | None:
    if not url:
        return None
    # Render a veces da postgres:// y SQLAlchemy quiere postgresql://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def ensure_tables_and_migrate():
    """
    Como usas SQL manual (text), create_all() NO crea nada.
    Aquí:
      - crea users y games si no existen
      - si games tiene columna "desc", la renombra a description
      - añade url y play si faltan
    """
    engine_name = db.engine.dialect.name  # 'postgresql' o 'sqlite'

    if engine_name == "postgresql":
        # 1) Crear tablas si no existen (ESQUEMA CORRECTO)
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """))

        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                year INT,
                description TEXT,
                img TEXT,
                url TEXT,
                play TEXT
            );
        """))

        # 2) Migración: si existe "desc" y no existe description -> renombrar
        db.session.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='games' AND column_name='desc'
            )
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='games' AND column_name='description'
            )
            THEN
                ALTER TABLE games RENAME COLUMN "desc" TO description;
            END IF;
        END $$;
        """))

        # 3) Añadir columnas si faltan
        db.session.execute(text("""ALTER TABLE games ADD COLUMN IF NOT EXISTS url TEXT;"""))
        db.session.execute(text("""ALTER TABLE games ADD COLUMN IF NOT EXISTS play TEXT;"""))
        db.session.execute(text("""ALTER TABLE games ADD COLUMN IF NOT EXISTS img TEXT;"""))
        db.session.execute(text("""ALTER TABLE games ADD COLUMN IF NOT EXISTS description TEXT;"""))

        db.session.commit()

    else:
        # SQLITE (local). Si vienes de una tabla antigua, lo más limpio es borrar games.db y recrear.
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """))
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                year INTEGER,
                description TEXT,
                img TEXT,
                url TEXT,
                play TEXT
            );
        """))
        db.session.commit()


def create_app():
    app = Flask(__name__, static_url_path="/static")

    # Secret keys
    app.secret_key = getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    # (Opcional) alargar expiración para no estar logueándote cada 15 min
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)

    # DB
    db_url = normalize_db_url(getenv("DATABASE_URL") or getenv("SQLALCHEMY_DATABASE_URI"))
    if not db_url:
        db_url = "sqlite:///games.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # JWT cookies cross-site (GitHub Pages -> Render)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = True      # en Render siempre HTTPS
    app.config["JWT_COOKIE_SAMESITE"] = "None"  # permite cross-site cookies
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    # CORS
    allowed_origins = [
        "https://aliciaandreumora.github.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )

    JWTManager(app)

    # Crear tablas + migración
    with app.app_context():
        ensure_tables_and_migrate()

    return app


app = create_app()

# IMPORTS después de crear app/db
import users
import games


@app.route("/", methods=["GET"])
def index():
    return jsonify({"msg": "API OK"}), 200


@app.route("/login", methods=["POST", "OPTIONS"])
def login_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user_ok = users.login(username, password)
    if not user_ok:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    resp = jsonify({"msg": "logged in"})
    set_access_cookies(resp, access_token)
    return resp, 200


@app.route("/logout", methods=["POST", "OPTIONS"])
def logout_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    resp = jsonify({"msg": "logout ok"})
    unset_jwt_cookies(resp)
    return resp, 200


@app.route("/register", methods=["POST", "OPTIONS"])
def register_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    register_ok, msg = users.register(username, password)
    if not register_ok:
        return jsonify({"msg": msg}), 409

    access_token = create_access_token(identity=username)
    resp = jsonify({"msg": f"User {username} registered and logged in"})
    set_access_cookies(resp, access_token)
    return resp, 200


@app.route("/me", methods=["GET", "OPTIONS"])
@jwt_required()
def me():
    if request.method == "OPTIONS":
        return make_response("", 204)
    return jsonify({"user": get_jwt_identity()}), 200


@app.route("/delete_user", methods=["POST", "OPTIONS"])
@jwt_required()
def delete_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    username = get_jwt_identity()
    if users.delete_user(username):
        resp = jsonify({"msg": f"User {username} deleted"})
        unset_jwt_cookies(resp)
        return resp, 200

    return jsonify({"msg": "Deletion not successful"}), 400


# Juegos
@app.route("/api/juegos", methods=["GET", "OPTIONS"])
@jwt_required()
def listar_juegos():
    if request.method == "OPTIONS":
        return make_response("", 204)
    return games.listar_juegos()


@app.route("/api/juegos", methods=["POST", "OPTIONS"])
@jwt_required()
def crear_juego():
    if request.method == "OPTIONS":
        return make_response("", 204)
    return games.crear_juego(request)


@app.route("/api/juegos/<int:id>", methods=["PUT", "OPTIONS"])
@jwt_required()
def editar_juego(id):
    if request.method == "OPTIONS":
        return make_response("", 204)
    return games.editar_juego(id, request)


@app.route("/api/juegos/<int:id>", methods=["DELETE", "OPTIONS"])
@jwt_required()
def eliminar_juego(id):
    if request.method == "OPTIONS":
        return make_response("", 204)
    return games.eliminar_juego(id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
