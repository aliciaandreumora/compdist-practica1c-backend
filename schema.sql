CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(48),
    password TEXT
);

CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    name VARCHAR(48),
    year INT,
    "desc" TEXT,
    img TEXT,
    url TEXT,
    play TEXT
);

