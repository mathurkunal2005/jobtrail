import sqlite3
import os
from datetime import datetime, timezone

# Always resolve the DB path relative to this file's own location,
# so it works correctly no matter what directory the server is launched from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobtrail.db")
RESUMES_DIR = os.path.join(BASE_DIR, "resumes")

def get_connection():
    """Opens a connection to our SQLite database file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn

def init_db():
    """Creates all tables if they don't already exist, and the resumes folder."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            date_applied TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            UNIQUE(company, role)
        )
    """)
    conn.commit()
    conn.close()

    os.makedirs(RESUMES_DIR, exist_ok=True)

def log_action(action: str, details: str):
    """Records one approved write action into the audit log."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (timestamp, action, details) VALUES (?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), action, details)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")