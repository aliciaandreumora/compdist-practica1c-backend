from os import getenv, path
from dotenv import load_dotenv
from flask import Flask, request, make_response, jsonify
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, set_access_cookies,
    unset_jwt_cookies, jwt_required, get_jwt_identity
)
from extensions import db

import users
import games


def _normalize_db_url(url: str) -> str:
    # Render a veces da postgres://... y SQLAlchemy prefiere postgresql://...
    if url and url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def init_db(app: Flask):
    """Crea tablas ejecutando schema.sql (idempotente)."""
    schema_path = path.join(path.abspath(path.dirname(__file__)), "schema.sql")
    with app.app_context():
        if path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                sql = f.read()
            # Ojo: con psycopg2, múltiples statements funcionan con autocommit de conexión
            conn = db.engine.raw_connection()
            try:
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(sql)
                cur.close()
            finally:
                conn.close()


def create_app():
    basedir = path.abspath(path.dirname(__file__))
    load_dotenv(path.join(basedir, ".env"))

    app = Flask(__name__, static_url_path="/static")

    # Secret keys
    app.secret_key = getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    # DB URL (Render: DATABASE_URL)
    db_url = getenv("DATABASE_URL") or getenv("SQLALCHEMY_DATABASE_URI")
    if not db_url:
        db_path = path.join(basedir, "games.db")
        db_url = "sqlite:///" + db_path

    app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_db_url(db_url)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # Bootstrap (si lo usas en templates)
    Bootstrap(app)

    # JWT en cookies (para GH Pages -> Render)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = getenv("JWT_COOKIE_SECURE", "true").lower() == "true"
    app.config["JWT_COOKIE_SAMESITE"] = "None"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    JWTManager(app)

    # CORS con credenciales
    # Pon FRONTEND_ORIGIN en Render: https://aliciaandreumora.github.io
    frontend_origin = getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    origins = [
        frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    CORS(
        app,
        origins=origins,
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )

    # Crear tablas en Postgres/SQLite
    init_db(app)

    return app


app = create_app()


@app.route("/", methods=["GET"])
def index():
    return jsonify({"msg": "API OK"}), 200


@app.route("/register", methods=["POST", "OPTIONS"])
def register_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if users.register(username, password):
        access_token = create_access_token(identity=username)
        resp = jsonify({"msg": f"User {username} registered and logged in"})
        set_access_cookies(resp, access_token)
        return resp, 200

    return jsonify({"msg": "Registration not successful"}), 401


@app.route("/login", methods=["POST", "OPTIONS"])
def login_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if users.login(username, password):
        access_token = create_access_token(identity=username)
        resp = jsonify({"msg": "logged in"})
        set_access_cookies(resp, access_token)
        return resp, 200

    return jsonify({"msg": "Bad username or password"}), 401


@app.route("/logout", methods=["POST", "OPTIONS"])
def logout_user():
    if request.method == "OPTIONS":
        return make_response("", 204)

    resp = jsonify({"msg": "logout ok"})
    unset_jwt_cookies(resp)
    return resp, 200


@app.route("/me", methods=["GET"])
@jwt_required()
def me():
    return jsonify({"user": get_jwt_identity()}), 200


@app.route("/delete_user", methods=["POST"])
@jwt_required()
def delete_user():
    username = get_jwt_identity()
    if users.delete_user(username):
        resp = jsonify({"msg": f"User {username} deleted"})
        unset_jwt_cookies(resp)
        return resp, 200
    return jsonify({"msg": f"Deletion of user {username} not successful"}), 401


@app.route("/api/juegos", methods=["GET"])
@jwt_required()
def listar_juegos():
    ret, code = games.listar_juegos()
    return jsonify(ret), code


@app.route("/api/juegos", methods=["POST", "OPTIONS"])
@jwt_required()
def crear_juego():
    if request.method == "OPTIONS":
        return make_response("", 204)
    ret, code = games.crear_juego(request)
    return jsonify(ret), code


@app.route("/api/juegos/<int:game_id>", methods=["PUT", "OPTIONS"])
@jwt_required()
def editar_juego(game_id):
    if request.method == "OPTIONS":
        return make_response("", 204)
    ret, code = games.editar_juego(game_id, request)
    return jsonify(ret), code


@app.route("/api/juegos/<int:game_id>", methods=["DELETE", "OPTIONS"])
@jwt_required()
def eliminar_juego(game_id):
    if request.method == "OPTIONS":
        return make_response("", 204)
    ret, code = games.eliminar_juego(game_id)
    return jsonify(ret), code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
