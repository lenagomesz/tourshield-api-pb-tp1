import sqlite3
from contextlib import contextmanager
from app.config import database_path


@contextmanager
def connect():
    connection = sqlite3.connect(database_path(), timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)))""")


def find_user(username: str):
    with connect() as db:
        return db.execute("SELECT username, password_hash, active FROM users WHERE username = ?",
                          (username,)).fetchone()
