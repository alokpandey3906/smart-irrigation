"""SQLite storage for recommendation history (standard library only)."""
import json
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT    NOT NULL,
    crop       TEXT    NOT NULL,
    stage      TEXT    NOT NULL,
    soil       TEXT    NOT NULL,
    method     TEXT    NOT NULL,
    inputs     TEXT    NOT NULL,
    level      TEXT    NOT NULL,
    message    TEXT    NOT NULL,
    litres     INTEGER NOT NULL,
    hours      REAL    NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        get_db().executescript(SCHEMA)


def save_record(inputs, result):
    db = get_db()
    db.execute(
        "INSERT INTO records (created_at, crop, stage, soil, method, inputs, level, message, litres, hours)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
         inputs["crop"], inputs["stage"], inputs["soil"], inputs["method"],
         json.dumps(inputs), result["level"], result["message"], result["litres"], result["hours"]),
    )
    db.commit()


def list_records(limit=100):
    rows = get_db().execute("SELECT * FROM records ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def clear_records():
    db = get_db()
    db.execute("DELETE FROM records")
    db.commit()
