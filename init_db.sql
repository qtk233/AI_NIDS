-- NIDS Database Schema (MySQL 8.0)
-- Run: mysql -u root -p < init_db.sql

CREATE DATABASE IF NOT EXISTS nids CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nids;

-- Detection logs: stores every flow classification result
CREATE TABLE IF NOT EXISTS detection_logs (
    id            CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    src_ip        VARCHAR(45) NOT NULL,
    dst_ip        VARCHAR(45) NOT NULL,
    src_port      INT,
    dst_port      INT,
    protocol      VARCHAR(10) NOT NULL,
    prediction    VARCHAR(50) NOT NULL,
    confidence    FLOAT NOT NULL,
    is_unknown    TINYINT(1) DEFAULT 0,
    is_attack     TINYINT(1) DEFAULT 0,
    stat_features JSON,
    payload_hash  VARCHAR(64),
    shap_data     JSON,
    attn_data     JSON,
    source        VARCHAR(20) DEFAULT 'pcap',
    model_version VARCHAR(20),

    INDEX idx_created_at (created_at DESC),
    INDEX idx_prediction (prediction),
    INDEX idx_src_ip (src_ip),
    INDEX idx_is_attack (is_attack)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Model versions: tracks deployed model checkpoints
CREATE TABLE IF NOT EXISTS model_versions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    version       VARCHAR(20) NOT NULL UNIQUE,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_path     TEXT NOT NULL,
    metrics       JSON NOT NULL,
    params_count  INT,
    is_active     TINYINT(1) DEFAULT 0
);

-- Experiments: synced from MLflow
CREATE TABLE IF NOT EXISTS experiments (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    run_name      VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hyperparams   JSON,
    metrics       JSON,
    artifacts_path TEXT
);
