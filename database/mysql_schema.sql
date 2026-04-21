-- ==========================================================
-- 🗄️  NARYAN AI — MySQL Schema
--     Run:  mysql -u root -p < database/mysql_schema.sql
-- ==========================================================

CREATE DATABASE IF NOT EXISTS narayan_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE narayan_ai;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(100)  NOT NULL UNIQUE,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history (with session + subject tracking)
CREATE TABLE IF NOT EXISTS chat_history (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    session_id VARCHAR(64),
    question   TEXT         NOT NULL,
    answer     TEXT         NOT NULL,
    intent     VARCHAR(50),
    subject    VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_user    (user_id)
);

-- Uploaded files metadata
CREATE TABLE IF NOT EXISTS files (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    subject   VARCHAR(100),
    topic     VARCHAR(200),
    file_name VARCHAR(255),
    file_path VARCHAR(255),
    file_type VARCHAR(20)   DEFAULT 'notes',
    added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student study progress
CREATE TABLE IF NOT EXISTS study_progress (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT,
    subject   VARCHAR(100),
    topic     VARCHAR(200),
    completed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_topic (user_id, subject, topic)
);

-- Test results
CREATE TABLE IF NOT EXISTS test_results (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT,
    subject  VARCHAR(100),
    score    INT,
    total    INT,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
