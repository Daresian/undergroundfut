import sqlite3
import time

DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            username TEXT,
            accepted_rules INTEGER DEFAULT 0,
            credits INTEGER DEFAULT 0,
            cooldown_until INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stake INTEGER,
            status TEXT,
            created_at INTEGER
        )
    """)

    conn.commit()
    conn.close()

def get_or_create_user(tg_id, username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row

    cur.execute("INSERT INTO users (tg_id, username) VALUES (?, ?)", (tg_id, username or ""))
    conn.commit()
    cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row

def set_rules_accepted(tg_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET accepted_rules = 1 WHERE tg_id = ?", (tg_id,))
    conn.commit()
    conn.close()

def user_has_accepted_rules(tg_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT accepted_rules FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and row["accepted_rules"] == 1)

def add_credits(tg_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits + ? WHERE tg_id = ?", (amount, tg_id))
    conn.commit()
    conn.close()

def remove_credits(tg_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits - ? WHERE tg_id = ?", (amount, tg_id))
    conn.commit()
    conn.close()

def create_payment(tg_id, stake):
    user = get_user_by_tg_id(tg_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO payments (user_id, stake, status, created_at) VALUES (?, ?, ?, ?)",
                (user["id"], stake, "pending", int(time.time())))
    conn.commit()
    conn.close()

def get_user_by_tg_id(tg_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_pending_payment_by_user(tg_id):
    user = get_user_by_tg_id(tg_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM payments WHERE user_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
                (user["id"],))
    row = cur.fetchone()
    conn.close()
    return row

def validate_payment(payment_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE payments SET status = 'validated' WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()

def reset_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = 0, cooldown_until = 0")
    conn.commit()
    conn.close()

