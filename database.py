# ==========================================================
# 🗄️  NARYAN AI — DATABASE LAYER
#     MySQL (production) | SQLite (dev fallback)
# ==========================================================

import os
import logging
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger("NARYAN_AI.db")

# Render environment variables से सेटिंग्स उठाना
USE_MYSQL = os.getenv("USE_MYSQL", "false").lower() == "true"
DB_PATH   = os.getenv("SQLITE_PATH", "narayan_ai.db")

MYSQL_CONFIG = {}
if USE_MYSQL:
    # MySQL settings (Aiven के लिए)
    MYSQL_CONFIG = {
        "host":     os.getenv("MYSQL_HOST"),
        "port":     int(os.getenv("MYSQL_PORT", 19706)),
        "user":     os.getenv("MYSQL_USER", "avnadmin"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE", "defaultdb"),
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

# ── Database Initialization ────────────────────────────────
def init_db():
    """Main function to create all tables."""
    try:
        if USE_MYSQL:
            _init_mysql()
        else:
            _init_sqlite()
        logger.info("Database initialised ✅")
    except Exception as e:
        logger.error(f"Failed to initialise database: {e}")
        raise e

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
    """)
    conn.commit()
    conn.close()

def _init_mysql():
    import mysql.connector
    # Direct connect to the database (Aiven already creates 'defaultdb')
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    c = conn.cursor()
    
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
        )"""
    ]
    
    for stmt in statements:
        c.execute(stmt)
    
    conn.commit()
    conn.close()
