from sqlalchemy import text
from flask import jsonify
from extensions import db


def listar_juegos():
    sql = text("""
        SELECT id, name, year, description, img, url, play
        FROM games
        ORDER BY id ASC
    """)
    rows = db.session.execute(sql).fetchall()
    data = [
        {
            "id": r[0],
            "name": r[1],
            "year": r[2],
            "description": r[3],
            "img": r[4],
            "url": r[5],
            "play": r[6],
        }
        for r in rows
    ]
    return jsonify(data), 200


def crear_juego(request):
    data = request.get_json() or {}
    name = data.get("name")
    year = data.get("year")
    description = data.get("description")
    img = data.get("img")
    url = data.get("url")
    play = data.get("play")

    if not name:
        return jsonify({"msg": "Missing 'name'"}), 400

    sql = text("""
        INSERT INTO games (name, year, description, img, url, play)
        VALUES (:name, :year, :description, :img, :url, :play)
        RETURNING id
    """)

    try:
        row = db.session.execute(sql, {
            "name": name, "year": year, "description": description,
            "img": img, "url": url, "play": play
        }).fetchone()
        db.session.commit()
        new_id = row[0] if row else None
        return jsonify({"msg": "created", "id": new_id}), 201
    except Exception:
        db.session.rollback()
        # fallback (por si alguna sqlite antigua no soporta RETURNING)
        sql2 = text("""
            INSERT INTO games (name, year, description, img, url, play)
            VALUES (:name, :year, :description, :img, :url, :play)
        """)
        db.session.execute(sql2, {
            "name": name, "year": year, "description": description,
            "img": img, "url": url, "play": play
        })
        db.session.commit()
        return jsonify({"msg": "created"}), 201


def editar_juego(id, request):
    data = request.get_json() or {}
    sql = text("""
        UPDATE games
        SET name=:name, year=:year, description=:description, img=:img, url=:url, play=:play
        WHERE id=:id
    """)
    db.session.execute(sql, {
        "id": id,
        "name": data.get("name"),
        "year": data.get("year"),
        "description": data.get("description"),
        "img": data.get("img"),
        "url": data.get("url"),
        "play": data.get("play"),
    })
    db.session.commit()
    return jsonify({"msg": "updated"}), 200


def eliminar_juego(id):
    sql = text("DELETE FROM games WHERE id=:id")
    db.session.execute(sql, {"id": id})
    db.session.commit()
    return jsonify({"msg": "deleted"}), 200
