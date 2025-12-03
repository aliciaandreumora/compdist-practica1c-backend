from flask import Blueprint, request, jsonify
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from extensions import db



games_bp = Blueprint("games_bp", __name__, url_prefix="/api/juegos")

def row_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "year": row[2],
        "desc": row[3],
        "img": row[4],
        "url": row[5],
        "play": row[6],
    }


def validate_payload(data, creating=True):
    if not isinstance(data, dict):
        return "Body JSON inválido"
    name = data.get("name")
    if not name or not isinstance(name, str):
        return "El campo 'name' es obligatorio y debe ser texto"
    year = data.get("year")
    if year is not None and not isinstance(year, int):
        return "El campo 'year' debe ser entero si se proporciona"
    return None


@games_bp.get("")
def listar_juegos():
    try:
        sql = text("""
            SELECT id, name, year, "desc", img, url, play
            FROM games
            ORDER BY id;
        """)
        res = db.session.execute(sql)
        rows = res.fetchall()
        return jsonify([row_to_dict(r) for r in rows]), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@games_bp.post("")
def crear_juego(request):
    try:
        data = request.get_json(force=True, silent=False)

        err = validate_payload(data, creating=True)
        if err:
            return jsonify({"error": err}), 400

        sql = text("""
            INSERT INTO games (name, year, "desc", img, url, play)
            VALUES (:name, :year, :description, :img, :url, :play)
            RETURNING id;
        """)
        res = db.session.execute(sql, {
            "name": data["name"],
            "year": data.get("year"),
            "description": data.get("desc"),
            "img": data.get("img"),
            "url": data.get("url"),
            "play": data.get("play"),
        })
        new_id = res.fetchone()[0]
        db.session.commit()
        return jsonify({"mensaje": "Juego añadido correctamente", "id": new_id}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@games_bp.put("/<int:game_id>")
def editar_juego(game_id, request):
    try:
        data = request.get_json(force=True, silent=False)

        err = validate_payload(data, creating=False)
        if err:
            return jsonify({"error": err}), 400

        exists = db.session.execute(
            text("SELECT 1 FROM games WHERE id=:id;"),
            {"id": game_id}
        ).fetchone()
        if not exists:
            return jsonify({"error": "Juego no encontrado"}), 404

        sql = text("""
            UPDATE games
            SET name=:name,
                year=:year,
                "desc"=:description,
                img=:img,
                url=:url,
                play=:play
            WHERE id=:id;
        """)
        db.session.execute(sql, {
            "name": data["name"],
            "year": data.get("year"),
            "description": data.get("desc"),
            "img": data.get("img"),
            "url": data.get("url"),
            "play": data.get("play"),
            "id": game_id
        })
        db.session.commit()
        return jsonify({"mensaje": "Juego actualizado correctamente"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@games_bp.delete("/<int:game_id>")
def eliminar_juego(game_id):
    try:
        exists = db.session.execute(
            text("SELECT 1 FROM games WHERE id=:id;"),
            {"id": game_id}
        ).fetchone()
        if not exists:
            return jsonify({"error": "Juego no encontrado"}), 404

        sql = text("DELETE FROM games WHERE id=:id;")
        db.session.execute(sql, {"id": game_id})
        db.session.commit()
        return jsonify({"mensaje": "Juego eliminado correctamente"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
