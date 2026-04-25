# utils/database.py

import sqlite3
import time
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id     INTEGER PRIMARY KEY,
        username        TEXT    DEFAULT '',
        full_name       TEXT    DEFAULT '',
        state           TEXT    DEFAULT 'IDLE',
        blocked_until   INTEGER DEFAULT 0,
        cooldown_until  INTEGER DEFAULT 0,
        accepted_rules  INTEGER DEFAULT 0,
        total_matches   INTEGER DEFAULT 0,
        total_wins      INTEGER DEFAULT 0,
        total_disputes  INTEGER DEFAULT 0,
        is_test         INTEGER DEFAULT 0,
        created_at      INTEGER DEFAULT (strftime('%s','now'))
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL,
        amount          INTEGER NOT NULL,
        status          TEXT    DEFAULT 'PENDING',
        created_at      INTEGER DEFAULT (strftime('%s','now')),
        expires_at      INTEGER NOT NULL,
        validated_at    INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(telegram_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS queue (
        user_id         INTEGER PRIMARY KEY,
        amount          INTEGER NOT NULL,
        joined_at       INTEGER DEFAULT (strftime('%s','now')),
        group_msg_id    INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(telegram_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id        TEXT    PRIMARY KEY,
        player1_id      INTEGER NOT NULL,
        player2_id      INTEGER NOT NULL,
        amount          INTEGER NOT NULL,
        status          TEXT    DEFAULT 'IN_PROGRESS',
        winner_id       INTEGER DEFAULT 0,
        group_msg_id    INTEGER DEFAULT 0,
        report_deadline INTEGER NOT NULL,
        created_at      INTEGER DEFAULT (strftime('%s','now')),
        closed_at       INTEGER DEFAULT 0,
        FOREIGN KEY (player1_id) REFERENCES users(telegram_id),
        FOREIGN KEY (player2_id) REFERENCES users(telegram_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS result_reports (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id        TEXT    NOT NULL,
        user_id         INTEGER NOT NULL,
        result          TEXT    NOT NULL,
        created_at      INTEGER DEFAULT (strftime('%s','now')),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (user_id) REFERENCES users(telegram_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS disputes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id        TEXT    NOT NULL UNIQUE,
        status          TEXT    DEFAULT 'OPEN',
        opened_at       INTEGER DEFAULT (strftime('%s','now')),
        deadline        INTEGER NOT NULL,
        resolved_at     INTEGER DEFAULT 0,
        verdict_user_id INTEGER DEFAULT 0,
        FOREIGN KEY (match_id) REFERENCES matches(match_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS anticheat_log (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL,
        code            TEXT    NOT NULL,
        detail          TEXT    DEFAULT '',
        created_at      INTEGER DEFAULT (strftime('%s','now')),
        FOREIGN KEY (user_id) REFERENCES users(telegram_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        action          TEXT    NOT NULL,
        target_user_id  INTEGER DEFAULT 0,
        match_id        TEXT    DEFAULT '',
        detail          TEXT    DEFAULT '',
        created_at      INTEGER DEFAULT (strftime('%s','now'))
    )""")

    conn.commit()
    conn.close()
    logger.info("DB inicializada.")


# ── USERS ─────────────────────────────────────────────────────────────────────

def upsert_user(telegram_id: int, username: str, full_name: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO users (telegram_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
        """, (telegram_id, username or "", full_name or ""))


def get_user(telegram_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()


def set_state(user_id: int, state: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET state = ? WHERE telegram_id = ?",
            (state, user_id)
        )


def get_state(user_id: int) -> str:
    u = get_user(user_id)
    return u["state"] if u else "IDLE"


def accept_rules(user_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET accepted_rules = 1, state = 'IDLE' WHERE telegram_id = ?",
            (user_id,)
        )


def set_blocked(user_id: int, hours: int):
    until = int(time.time()) + hours * 3600
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET state='BLOCKED', blocked_until=? WHERE telegram_id=?",
            (until, user_id)
        )


def set_cooldown(user_id: int, minutes: int):
    until = int(time.time()) + minutes * 60
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET cooldown_until=? WHERE telegram_id=?",
            (until, user_id)
        )


def reset_user(user_id: int):
    """Reset completo para usuarios de prueba."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE users SET state='IDLE', accepted_rules=0,
               blocked_until=0, cooldown_until=0 WHERE telegram_id=?""",
            (user_id,)
        )
        conn.execute("DELETE FROM queue WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM payments WHERE user_id=? AND status='PENDING'", (user_id,))


# ── PAYMENTS ──────────────────────────────────────────────────────────────────

def create_payment(user_id: int, amount: int, timeout_minutes: int) -> int:
    expires = int(time.time()) + timeout_minutes * 60
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO payments (user_id, amount, expires_at) VALUES (?,?,?)",
            (user_id, amount, expires)
        )
        return cur.lastrowid


def get_payment(payment_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        ).fetchone()


def validate_payment(payment_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE payments SET status='VALIDATED', validated_at=? WHERE id=?",
            (int(time.time()), payment_id)
        )


def expire_payment(payment_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE payments SET status='EXPIRED' WHERE id=?", (payment_id,)
        )


# ── QUEUE ─────────────────────────────────────────────────────────────────────

def add_to_queue(user_id: int, amount: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO queue (user_id, amount) VALUES (?,?)",
            (user_id, amount)
        )


def set_queue_msg(user_id: int, msg_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE queue SET group_msg_id=? WHERE user_id=?",
            (msg_id, user_id)
        )


def remove_from_queue(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM queue WHERE user_id=?", (user_id,))


def find_rival(user_id: int, amount: int):
    """Devuelve el primer jugador en cola con el mismo stake distinto al solicitante."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.user_id, q.group_msg_id, u.username, u.full_name
            FROM queue q
            JOIN users u ON q.user_id = u.telegram_id
            WHERE q.amount = ? AND q.user_id != ?
            ORDER BY q.joined_at ASC
            LIMIT 1
        """, (amount, user_id)).fetchone()


# ── MATCHES ───────────────────────────────────────────────────────────────────

def create_match(match_id: str, p1: int, p2: int, amount: int, timeout_minutes: int):
    deadline = int(time.time()) + timeout_minutes * 60
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO matches (match_id, player1_id, player2_id, amount, report_deadline)
            VALUES (?,?,?,?,?)
        """, (match_id, p1, p2, amount, deadline))


def get_match(match_id: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM matches WHERE match_id=?", (match_id,)
        ).fetchone()


def get_active_match(user_id: int):
    with get_conn() as conn:
        return conn.execute("""
            SELECT * FROM matches
            WHERE (player1_id=? OR player2_id=?)
              AND status='IN_PROGRESS'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, user_id)).fetchone()


def close_match(match_id: str, winner_id: int, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE matches SET status=?, winner_id=?, closed_at=? WHERE match_id=?",
            (status, winner_id, int(time.time()), match_id)
        )
        if winner_id:
            conn.execute(
                "UPDATE users SET total_matches=total_matches+1, "
                "total_wins=total_wins+1 WHERE telegram_id=?", (winner_id,)
            )
        # Actualizar total de partidas para ambos jugadores
        match = conn.execute(
            "SELECT player1_id, player2_id FROM matches WHERE match_id=?",
            (match_id,)
        ).fetchone()
        if match and winner_id:
            loser = match["player2_id"] if winner_id == match["player1_id"] else match["player1_id"]
            conn.execute(
                "UPDATE users SET total_matches=total_matches+1 WHERE telegram_id=?",
                (loser,)
            )


def set_match_group_msg(match_id: str, msg_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE matches SET group_msg_id=? WHERE match_id=?",
            (msg_id, match_id)
        )


# ── RESULTS ───────────────────────────────────────────────────────────────────

def save_report(match_id: str, user_id: int, result: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO result_reports (match_id, user_id, result) VALUES (?,?,?)",
            (match_id, user_id, result)
        )


def get_reports(match_id: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM result_reports WHERE match_id=?", (match_id,)
        ).fetchall()


def has_reported(match_id: str, user_id: int) -> bool:
    with get_conn() as conn:
        r = conn.execute(
            "SELECT id FROM result_reports WHERE match_id=? AND user_id=?",
            (match_id, user_id)
        ).fetchone()
        return r is not None


# ── DISPUTES ──────────────────────────────────────────────────────────────────

def open_dispute(match_id: str, hours: int):
    deadline = int(time.time()) + hours * 3600
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO disputes (match_id, deadline) VALUES (?,?)",
            (match_id, deadline)
        )
        conn.execute(
            "UPDATE matches SET status='DISPUTED' WHERE match_id=?",
            (match_id,)
        )


def close_dispute(match_id: str, verdict_user_id: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE disputes SET status='RESOLVED', resolved_at=?, verdict_user_id=?
            WHERE match_id=?
        """, (int(time.time()), verdict_user_id, match_id))


def get_open_disputes():
    with get_conn() as conn:
        return conn.execute("""
            SELECT d.match_id, d.deadline,
                   m.player1_id, m.player2_id, m.amount,
                   u1.username AS p1_name, u2.username AS p2_name
            FROM disputes d
            JOIN matches m ON d.match_id = m.match_id
            JOIN users u1 ON m.player1_id = u1.telegram_id
            JOIN users u2 ON m.player2_id = u2.telegram_id
            WHERE d.status = 'OPEN'
            ORDER BY d.deadline ASC
        """).fetchall()


# ── ANTICHEAT / AUDIT ─────────────────────────────────────────────────────────

def log_anticheat(user_id: int, code: str, detail: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO anticheat_log (user_id, code, detail) VALUES (?,?,?)",
            (user_id, code, detail)
        )


def log_audit(action: str, target_user_id: int = 0, match_id: str = "", detail: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (action, target_user_id, match_id, detail) VALUES (?,?,?,?)",
            (action, target_user_id, match_id, detail)
        )
