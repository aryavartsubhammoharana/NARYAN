# ==========================================================
# 🗄️  NARYAN AI — DATABASE LAYER
#     MySQL (production) | SQLite (dev fallback)
# ==========================================================

import os
import logging
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger("NARYAN_AI.db")

USE_MYSQL = os.getenv("USE_MYSQL", "false").lower() == "true"
DB_PATH   = os.getenv("SQLITE_PATH", "narayan_ai.db")

MYSQL_CONFIG = {}
if USE_MYSQL:
    import mysql.connector
    MYSQL_CONFIG = {
        "host":     os.getenv("MYSQL_HOST", "localhost"),
        "port":     int(os.getenv("MYSQL_PORT", 3306)),
        "user":     os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "narayan_ai"),
    }

# ── Context manager ────────────────────────────────────────
@contextmanager
def get_db():
    if USE_MYSQL:
        import mysql.connector
        conn   = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()


def init_db():
    """Create all tables if they don't exist."""
    if USE_MYSQL:
        _init_mysql()
    else:
        _init_sqlite()
    logger.info("Database initialised ✅")


def _init_sqlite():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name       TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            branch          TEXT,
            roll_number     TEXT UNIQUE,
            is_verified     INTEGER DEFAULT 0,
            verify_token    TEXT,
            reset_token     TEXT,
            reset_expires   DATETIME,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            session_id TEXT,
            question   TEXT NOT NULL,
            answer     TEXT NOT NULL,
            intent     TEXT,
            subject    TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS files (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            subject   TEXT,
            topic     TEXT,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            added_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS study_progress (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            subject   TEXT,
            topic     TEXT,
            completed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            subject   TEXT,
            score     INTEGER,
            total     INTEGER,
            taken_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def _init_mysql():
    import mysql.connector
    cfg = dict(MYSQL_CONFIG)
    db  = cfg.pop("database")
    conn = mysql.connector.connect(**cfg)
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{db}`")
    c.execute(f"USE `{db}`")
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            full_name     VARCHAR(150) NOT NULL,
            email         VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            branch        VARCHAR(100),
            roll_number   VARCHAR(50) UNIQUE,
            is_verified   TINYINT(1) DEFAULT 0,
            verify_token  VARCHAR(255),
            reset_token   VARCHAR(255),
            reset_expires DATETIME,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS chat_history (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT,
            session_id VARCHAR(64),
            question   TEXT,
            answer     TEXT,
            intent     VARCHAR(50),
            subject    VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS files (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            subject   VARCHAR(100),
            topic     VARCHAR(200),
            file_name VARCHAR(255),
            file_path VARCHAR(255),
            file_type VARCHAR(20),
            added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS study_progress (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            user_id   INT,
            subject   VARCHAR(100),
            topic     VARCHAR(200),
            completed BOOLEAN DEFAULT FALSE
        )""",
        """CREATE TABLE IF NOT EXISTS test_results (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            user_id  INT,
            subject  VARCHAR(100),
            score    INT,
            total    INT,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    for stmt in statements:
        c.execute(stmt)
    conn.commit()
    conn.close()
