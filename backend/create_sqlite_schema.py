#!/usr/bin/env python
"""Create SQLite schema for local development."""

import sqlite3
import os

DB_PATH = "test.db"

# Remove old DB
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Enable foreign keys
c.execute("PRAGMA foreign_keys = ON")

# Core tables
c.execute("""
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    email_verified BOOLEAN DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    is_superuser BOOLEAN DEFAULT 0,
    is_2fa_enabled BOOLEAN DEFAULT 0,
    totp_secret TEXT,
    country_code TEXT DEFAULT 'AR',
    preferred_currency TEXT DEFAULT 'ARS',
    timezone TEXT DEFAULT 'America/Argentina/Buenos_Aires',
    billing_address TEXT DEFAULT '{}',
    payment_methods TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE businesses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT UNIQUE,
    description TEXT,
    website TEXT,
    logo_url TEXT,
    localization_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()

print("SQLite schema created: test.db")
