CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(48) UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    name VARCHAR(48),
    year INT,
    "desc" TEXT,
    img TEXT,
    url TEXT,
    play TEXT
);
