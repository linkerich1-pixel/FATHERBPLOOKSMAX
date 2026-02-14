import sqlite3
from datetime import datetime

DB = "data/database.sqlite"

def connect():
    return sqlite3.connect(DB)

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        pro INTEGER DEFAULT 0,
        daily_count INTEGER DEFAULT 0,
        last_reset TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        score REAL,
        tier TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def check_limit(user_id):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT pro, daily_count, last_reset FROM users WHERE id=?", (user_id,))
    row = c.fetchone()

    today = datetime.now().date().isoformat()

    if not row:
        c.execute("INSERT INTO users (id, last_reset) VALUES (?, ?)", (user_id, today))
        conn.commit()
        conn.close()
        return True

    pro, daily_count, last_reset = row

    if pro:
        conn.close()
        return True

    if last_reset != today:
        c.execute("UPDATE users SET daily_count=0, last_reset=? WHERE id=?", (today, user_id))
        conn.commit()
        conn.close()
        return True

    if daily_count >= 3:
        conn.close()
        return False

    conn.close()
    return True

def increment_usage(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE users SET daily_count = daily_count + 1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
