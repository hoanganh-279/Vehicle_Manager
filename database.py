"""
═══════════════════════════════════════════════════════════════════════════
DATABASE.PY - PostgreSQL Connection Pool & Schema Management
═══════════════════════════════════════════════════════════════════════════
Production-ready database utilities for Render deployment
"""

import os
import logging
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONNECTION POOL
# ═══════════════════════════════════════════════════════════════════════════

_connection_pool = None

def init_connection_pool():
    """Initialize PostgreSQL connection pool"""
    global _connection_pool
    
    if _connection_pool is not None:
        return _connection_pool
    
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    try:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url
        )
        logger.info("✅ PostgreSQL connection pool initialized")
        return _connection_pool
    except Exception as e:
        logger.error(f"❌ Failed to initialize connection pool: {e}")
        raise

def get_connection():
    """Get connection from pool"""
    global _connection_pool
    
    if _connection_pool is None:
        init_connection_pool()
    
    try:
        conn = _connection_pool.getconn()
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to get connection: {e}")
        raise

def return_connection(conn):
    """Return connection to pool"""
    global _connection_pool
    
    if _connection_pool and conn:
        _connection_pool.putconn(conn)

@contextmanager
def get_db_connection():
    """Context manager for database connection"""
    conn = get_connection()
    try:
        yield conn
    finally:
        return_connection(conn)

@contextmanager
def get_db_cursor(commit=True):
    """Context manager for database cursor with auto-commit"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Database error: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)

# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA CREATION
# ═══════════════════════════════════════════════════════════════════════════

def create_tables():
    """
    Create all required tables if they don't exist
    This runs automatically when app starts
    """
    
    schema_sql = """
    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: users (Admin users)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(200),
        email VARCHAR(200),
        role VARCHAR(50) DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: parking_config (System configuration)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS parking_config (
        id SERIAL PRIMARY KEY,
        motorbike_capacity INTEGER DEFAULT 100,
        car_capacity INTEGER DEFAULT 50,
        motorbike_rate INTEGER DEFAULT 5000,
        car_rate INTEGER DEFAULT 15000,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: pricing_rules (Dynamic pricing)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS pricing_rules (
        id SERIAL PRIMARY KEY,
        vehicle_type VARCHAR(50) NOT NULL,
        time_from TIME NOT NULL,
        time_to TIME NOT NULL,
        rate INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: cards (Member cards)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS cards (
        id SERIAL PRIMARY KEY,
        card_number VARCHAR(50) UNIQUE NOT NULL,
        owner_name VARCHAR(200),
        phone VARCHAR(20),
        email VARCHAR(200),
        balance DECIMAL(18, 2) DEFAULT 0,
        status VARCHAR(50) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_cards_card_number ON cards(card_number);
    CREATE INDEX IF NOT EXISTS idx_cards_phone ON cards(phone);

    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: vehicles (Parking records)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS vehicles (
        id SERIAL PRIMARY KEY,
        license_plate VARCHAR(20) NOT NULL,
        plate_color VARCHAR(50),
        vehicle_type VARCHAR(50) NOT NULL,
        plate_type VARCHAR(50),
        status VARCHAR(50) DEFAULT 'parked',
        entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exit_time TIMESTAMP,
        actual_fee DECIMAL(18, 2),
        payment_status VARCHAR(50) DEFAULT 'unpaid',
        payment_method VARCHAR(50),
        card_id INTEGER REFERENCES cards(id),
        spot_id INTEGER,
        parking_spot_id INTEGER,
        momo_trans_id VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_vehicles_license_plate ON vehicles(license_plate);
    CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
    CREATE INDEX IF NOT EXISTS idx_vehicles_entry_time ON vehicles(entry_time);
    CREATE INDEX IF NOT EXISTS idx_vehicles_card_id ON vehicles(card_id);

    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: topup_transactions (Card topup history)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS topup_transactions (
        id SERIAL PRIMARY KEY,
        card_id INTEGER NOT NULL REFERENCES cards(id),
        amount DECIMAL(18, 2) NOT NULL,
        payment_method VARCHAR(50) DEFAULT 'momo',
        status VARCHAR(50) DEFAULT 'pending',
        transaction_id VARCHAR(100) UNIQUE NOT NULL,
        momo_trans_id VARCHAR(100) UNIQUE,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_topup_card_id ON topup_transactions(card_id);
    CREATE INDEX IF NOT EXISTS idx_topup_transaction_id ON topup_transactions(transaction_id);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_topup_momo_trans_id ON topup_transactions(momo_trans_id) WHERE momo_trans_id IS NOT NULL;

    -- ═══════════════════════════════════════════════════════════════════════
    -- TABLE: balance_history (Audit trail)
    -- ═══════════════════════════════════════════════════════════════════════
    CREATE TABLE IF NOT EXISTS balance_history (
        id SERIAL PRIMARY KEY,
        card_id INTEGER NOT NULL REFERENCES cards(id),
        amount DECIMAL(18, 2) NOT NULL,
        balance_before DECIMAL(18, 2) NOT NULL,
        balance_after DECIMAL(18, 2) NOT NULL,
        type VARCHAR(50) NOT NULL,
        description TEXT,
        transaction_id VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(100),
        ip_address VARCHAR(50)
    );

    CREATE INDEX IF NOT EXISTS idx_balance_history_card_id ON balance_history(card_id);
    CREATE INDEX IF NOT EXISTS idx_balance_history_created_at ON balance_history(created_at);

    -- ═══════════════════════════════════════════════════════════════════════
    -- INSERT DEFAULT DATA (if tables are empty)
    -- ═══════════════════════════════════════════════════════════════════════
    
    -- Default parking config
    INSERT INTO parking_config (motorbike_capacity, car_capacity, motorbike_rate, car_rate)
    SELECT 100, 50, 5000, 15000
    WHERE NOT EXISTS (SELECT 1 FROM parking_config LIMIT 1);

    -- Default admin user (password: admin123)
    INSERT INTO users (username, password_hash, full_name, email, role)
    SELECT 'admin', 'admin123', 'Administrator', 'admin@parking.com', 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
    """
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(schema_sql)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# QUERY HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def query_db(query, args=None, one=False):
    """Execute SELECT query and return results as dict"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, args or ())
            
            if one:
                result = cursor.fetchone()
                return dict(result) if result else None
            else:
                results = cursor.fetchall()
                return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"❌ Query error: {e}")
        raise

def execute_db(query, args=None):
    """Execute INSERT/UPDATE/DELETE query"""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, args or ())
            
            # Get last inserted ID for INSERT queries
            if query.strip().upper().startswith('INSERT'):
                cursor.execute("SELECT lastval()")
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                return cursor.rowcount
    except Exception as e:
        logger.error(f"❌ Execute error: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════

def close_connection_pool():
    """Close all connections in pool"""
    global _connection_pool
    
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("✅ Connection pool closed")
