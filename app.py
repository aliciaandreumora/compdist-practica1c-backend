from os import getenv, path
from dotenv import load_dotenv
from flask import Flask, redirect, request, make_response, jsonify
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token, set_access_cookies,
                                unset_jwt_cookies, jwt_required, get_jwt_identity)
from extensions import db
print("DB instance in app.py:", id(db))


def create_app():
    basedir = path.abspath(path.dirname(__file__))
    env_dir = path.join(basedir, '.env')
    load_dotenv(env_dir)

    c_app = Flask(__name__, '/static')
    c_app.secret_key = getenv('SECRET_KEY')
    c_app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
    db.init_app(c_app)

    c_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    Bootstrap(c_app)

    c_app.config["JWT_SECRET_KEY"] = getenv('JWT_SECRET_KEY')
    c_app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    c_app.config["JWT_COOKIE_SECURE"] = False
    c_app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    c_app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    CORS(c_app,
     resources={r"/*": {"origins": [
         "http://localhost:5173",
         "http://localhost:5174",
         "http://127.0.0.1:5173",
         "http://127.0.0.1:5174"
     ]}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])



    #CORS(app,
    #     origins=["http://localhost:5173"],
    #     supports_credentials=True)

    jwt = JWTManager(c_app)

    return c_app, db


app, db = create_app()


@app.route('/login', methods=['POST', 'OPTIONS'])
def login_user():
    if request.method == "OPTIONS":
        response = make_response("", 204)
        return response

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user_ok = users.login(username, password)

    if user_ok:
        access_token = create_access_token(identity=username)
        response = jsonify({"msg": "logged in"})
        set_access_cookies(response, access_token)
        print("login response", response)
        return response
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@app.post("/logout")
def logout_user():
    print('LOGOUT')
    resp = jsonify({"msg": "logout ok"})
    unset_jwt_cookies(resp)
    return resp


@app.route('/register', methods=['POST'])
def register_user():
    print('REGISTER')
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username and password:
        register_ok = users.register(username, password)
        if register_ok:
            access_token = create_access_token(identity=username)
            response = jsonify({"msg": f"User {username} registered and logged in"})
            set_access_cookies(response, access_token)
            print("login response", response)
            return response

    return jsonify({"msg": "Registration not successful"}), 401


@app.route('/delete_user', methods=['POST'])
@jwt_required()
def delete_user():
    username = get_jwt_identity()
    deletion_ok = users.delete_user(username)
    if deletion_ok:
        response = jsonify({"msg": f"User {username} deleted"})
        unset_jwt_cookies(response)
        return response, 200

    return jsonify({"msg": f"Deletion of user {username} not successful"}), 401


@app.route("/me", methods=["GET"])
@jwt_required()
def me():
    return jsonify({"user": get_jwt_identity()}), 200


#@app.route("/protected", methods=["GET"])
#@jwt_required()
#def protected():
#    print("PROTECTED ENTERED")
#    current_user = get_jwt_identity()
#    return jsonify({"user": current_user}), 200


@app.route("/api/juegos", methods=["GET"])
@jwt_required()
def listar_juegos():
    ret, codigo = games.listar_juegos()
    return ret, codigo


@app.route("/api/juegos", methods=["POST", "OPTIONS"])
@jwt_required()
def crear_juego():
    print("CREAR JUEGO", 1)
    if request.method == "OPTIONS":
        response = make_response("", 204)
        return response

    print("CREAR JUEGO", 2)
    data = request.json
    print(data)
    ret, codigo = games.crear_juego(request)
    print("CREAR JUEGO", 3)
    print(ret, codigo)
    return ret, codigo


@app.route("/api/juegos/<int:id>", methods=["PUT"])
@jwt_required()
def editar_juego(id):
    data = request.json
    ret, codigo = games.editar_juego(id, request)
    return ret, codigo


@app.route("/api/juegos/<int:id>", methods=["DELETE"])
@jwt_required()
def eliminar_juego(id):
    ret, codigo = games.eliminar_juego(id)
    return ret, codigo


import users
import games


if __name__ == '__main__':
    app.run()
