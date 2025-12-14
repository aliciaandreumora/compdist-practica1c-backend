from sqlalchemy import text
from extensions import db

def listar_juegos():
    rows = db.session.execute(
        text('SELECT id, name, year, "desc", img, url, play FROM games ORDER BY id')
    ).fetchall()

    juegos = []
    for r in rows:
        juegos.append({
            "id": r[0],
            "name": r[1],
            "year": r[2],
            "desc": r[3],
            "img": r[4],
            "url": r[5],
            "play": r[6],
        })
    return juegos, 200


def crear_juego(request):
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    year = data.get("year")
    desc = data.get("desc")
    img = data.get("img")
    url = data.get("url")
    play = data.get("play")

    db.session.execute(
        text('INSERT INTO games (name, year, "desc", img, url, play) VALUES (:n,:y,:d,:i,:u,:p)'),
        {"n": name, "y": year, "d": desc, "i": img, "u": url, "p": play}
    )
    db.session.commit()
    return {"msg": "Game created"}, 201


def editar_juego(game_id: int, request):
    data = request.get_json(silent=True) or {}

    db.session.execute(
        text('UPDATE games SET name=:n, year=:y, "desc"=:d, img=:i, url=:u, play=:p WHERE id=:id'),
        {
            "id": game_id,
            "n": data.get("name"),
            "y": data.get("year"),
            "d": data.get("desc"),
            "i": data.get("img"),
            "u": data.get("url"),
            "p": data.get("play"),
        }
    )
    db.session.commit()
    return {"msg": "Game updated"}, 200


def eliminar_juego(game_id: int):
    db.session.execute(
        text("DELETE FROM games WHERE id=:id"),
        {"id": game_id}
    )
    db.session.commit()
    return {"msg": "Game deleted"}, 200
