import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "spendly.db"

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()

    if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None:
        conn.close()
        return

    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cursor.lastrowid

    today = date.today()

    def day(d):
        return today.replace(day=d).isoformat()

    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 520.0, "Food", day(1), "Groceries"),
            (user_id, 340.0, "Transport", day(3), "Metro card recharge"),
            (user_id, 1500.0, "Bills", day(6), "Internet and mobile"),
            (user_id, 780.0, "Health", day(9), "Medicine and checkup"),
            (user_id, 450.0, "Entertainment", day(12), "Movie tickets"),
            (user_id, 2199.0, "Shopping", day(15), "New shoes"),
            (user_id, 260.0, "Food", day(19), "Dinner out"),
            (user_id, 300.0, "Other", day(24), "Gift wrapping and cards"),
        ],
    )

    conn.commit()
    conn.close()
