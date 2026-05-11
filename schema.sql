DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

DROP TABLE IF EXISTS locations;
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    fish_count INTEGER NOT NULL,
    description TEXT,
    image_filename TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

DROP TABLE IF EXISTS fish;
CREATE TABLE fish (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    image_filename TEXT,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);

DROP TABLE IF EXISTS food_logs;
CREATE TABLE food_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fish_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    pellets INTEGER NOT NULL DEFAULT 0,
    UNIQUE(fish_id, date),
    FOREIGN KEY(fish_id) REFERENCES fish(id)
);
