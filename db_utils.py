"""
═══════════════════════════════════════════════════════════════════════════
DATABASE UTILITIES - DUAL-MODE SUPPORT
═══════════════════════════════════════════════════════════════════════════
Tự động nhận diện môi trường:
- Nếu có DATABASE_URL → PostgreSQL (Render)
- Nếu không → SQL Server (Local)
═══════════════════════════════════════════════════════════════════════════
"""

import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# DETECT DATABASE TYPE
# ═══════════════════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv('DATABASE_URL')
IS_POSTGRESQL = DATABASE_URL is not None

if IS_POSTGRESQL:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import pool
    logger.info("🐘 Using PostgreSQL (Render)")
else:
    import pyodbc
    logger.info("🗄️  Using SQL Server (Local)")

# ═══════════════════════════════════════════════════════════════════════════
# CONNECTION POOL (PostgreSQL only)
# ═══════════════════════════════════════════════════════════════════════════

_pg_pool = None

def init_pg_pool():
    """Initialize PostgreSQL connection pool"""
    global _pg_pool
    if IS_POSTGRESQL and _pg_pool is None:
        try:
            _pg_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            logger.info("✅ PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize PostgreSQL pool: {e}")
            raise

def get_pg_connection():
    """Get connection from pool"""
    if _pg_pool is None:
        init_pg_pool()
    return _pg_pool.getconn()

def return_pg_connection(conn):
    """Return connection to pool"""
    if _pg_pool:
        _pg_pool.putconn(conn)

# ═══════════════════════════════════════════════════════════════════════════
# GET DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════

def get_db():
    """
    Tạo kết nối database (tự động nhận diện môi trường)
    
    Returns:
        connection object (psycopg2 hoặc pyodbc)
    """
    if IS_POSTGRESQL:
        # PostgreSQL (Render)
        conn = get_pg_connection()
        conn.autocommit = False  # Explicit transaction control
        return conn
    else:
        # SQL Server (Local)
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={os.getenv("DB_SERVER", r"LAPTOP-3J6T1I18\SQLEXPRESS01")};'
            f'DATABASE={os.getenv("DB_DATABASE", "ParkingManagement")};'
            f'Trusted_Connection=yes;'
        )
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16-le')
        conn.setencoding(encoding='utf-16-le')
        return conn

@contextmanager
def get_db_context():
    """
    Context manager for database connection
    
    Usage:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cards")
    """
    conn = get_db()
    try:
        yield conn
    finally:
        if IS_POSTGRESQL:
            return_pg_connection(conn)
        else:
            conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# SQL SYNTAX HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def sql_limit(n):
    """
    Convert TOP N to LIMIT N
    
    Usage:
        # SQL Server: SELECT TOP 10 * FROM vehicles
        # PostgreSQL: SELECT * FROM vehicles LIMIT 10
        
        query = f"SELECT {sql_limit(10)} * FROM vehicles"
    """
    if IS_POSTGRESQL:
        return ""  # Use LIMIT at end
    else:
        return f"TOP {n}"

def sql_limit_clause(n):
    """
    Get LIMIT clause for end of query
    
    Usage:
        query = f"SELECT * FROM vehicles {sql_limit_clause(10)}"
    """
    if IS_POSTGRESQL:
        return f"LIMIT {n}"
    else:
        return ""  # Already used TOP

def sql_now():
    """
    Get current timestamp function
    
    SQL Server: GETDATE()
    PostgreSQL: CURRENT_TIMESTAMP or NOW()
    """
    if IS_POSTGRESQL:
        return "CURRENT_TIMESTAMP"
    else:
        return "GETDATE()"

def sql_isnull(column, default):
    """
    Handle NULL values
    
    SQL Server: ISNULL(column, default)
    PostgreSQL: COALESCE(column, default)
    """
    if IS_POSTGRESQL:
        return f"COALESCE({column}, {default})"
    else:
        return f"ISNULL({column}, {default})"

def sql_lock_row():
    """
    Row locking syntax
    
    SQL Server: WITH (UPDLOCK, ROWLOCK)
    PostgreSQL: FOR UPDATE
    """
    if IS_POSTGRESQL:
        return "FOR UPDATE"
    else:
        return "WITH (UPDLOCK, ROWLOCK)"

def sql_identity():
    """
    Auto-increment column type
    
    SQL Server: IDENTITY(1,1)
    PostgreSQL: SERIAL
    """
    if IS_POSTGRESQL:
        return "SERIAL"
    else:
        return "IDENTITY(1,1)"

def sql_varchar(length):
    """
    Variable character type
    
    SQL Server: NVARCHAR(length)
    PostgreSQL: VARCHAR(length)
    """
    if IS_POSTGRESQL:
        return f"VARCHAR({length})"
    else:
        return f"NVARCHAR({length})"

def sql_datetime():
    """
    Datetime column type
    
    SQL Server: DATETIME
    PostgreSQL: TIMESTAMP
    """
    if IS_POSTGRESQL:
        return "TIMESTAMP"
    else:
        return "DATETIME"

# ═══════════════════════════════════════════════════════════════════════════
# QUERY HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def dict_from_row(row, cursor):
    """
    Convert database row to dictionary
    
    Args:
        row: database row object
        cursor: database cursor
    
    Returns:
        dict with column names as keys
    """
    if row is None:
        return None
    
    if IS_POSTGRESQL:
        # PostgreSQL with RealDictCursor returns dict directly
        if isinstance(row, dict):
            return row
        # Otherwise convert manually
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    else:
        # pyodbc
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

def query_db(query, args=None, one=False):
    """
    Execute SELECT query and return results
    
    Args:
        query: SQL query string
        args: Query parameters (list or tuple)
        one: Return single row (True) or all rows (False)
    
    Returns:
        dict or list of dicts
    """
    conn = get_db()
    try:
        if IS_POSTGRESQL:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cursor = conn.cursor()
        
        if args:
            cursor.execute(query, args)
        else:
            cursor.execute(query)
        
        if one:
            row = cursor.fetchone()
            if IS_POSTGRESQL:
                return dict(row) if row else None
            else:
                return dict_from_row(row, cursor) if row else None
        else:
            rows = cursor.fetchall()
            if IS_POSTGRESQL:
                return [dict(row) for row in rows]
            else:
                return [dict_from_row(row, cursor) for row in rows]
    finally:
        if IS_POSTGRESQL:
            return_pg_connection(conn)
        else:
            conn.close()

def execute_db(query, args=None):
    """
    Execute INSERT/UPDATE/DELETE query
    
    Args:
        query: SQL query string
        args: Query parameters (list or tuple)
    
    Returns:
        Last inserted ID (for INSERT) or affected rows count
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        if args:
            cursor.execute(query, args)
        else:
            cursor.execute(query)
        
        conn.commit()
        
        # Get last inserted ID
        if IS_POSTGRESQL:
            # PostgreSQL: Use RETURNING id
            if 'RETURNING' in query.upper():
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                # For INSERT without RETURNING, get last value
                if 'INSERT' in query.upper():
                    cursor.execute("SELECT lastval()")
                    return cursor.fetchone()[0]
                else:
                    return cursor.rowcount
        else:
            # SQL Server: Use SCOPE_IDENTITY()
            if 'INSERT' in query.upper():
                cursor.execute("SELECT SCOPE_IDENTITY()")
                result = cursor.fetchone()
                return int(result[0]) if result and result[0] else None
            else:
                return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Database error: {e}")
        raise
    finally:
        if IS_POSTGRESQL:
            return_pg_connection(conn)
        else:
            conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

@contextmanager
def transaction():
    """
    Context manager for database transaction
    
    Usage:
        with transaction() as (conn, cursor):
            cursor.execute("UPDATE cards SET balance = balance + 100 WHERE id = 1")
            cursor.execute("INSERT INTO balance_history (...) VALUES (...)")
            # Auto-commit on success, auto-rollback on exception
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        yield conn, cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Transaction failed: {e}")
        raise
    finally:
        if IS_POSTGRESQL:
            return_pg_connection(conn)
        else:
            conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def init_db():
    """Initialize database (create pool for PostgreSQL)"""
    if IS_POSTGRESQL:
        init_pg_pool()
        logger.info("✅ Database initialized (PostgreSQL)")
    else:
        logger.info("✅ Database initialized (SQL Server)")

# ═══════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════

def close_db():
    """Close database connections (cleanup pool for PostgreSQL)"""
    global _pg_pool
    if IS_POSTGRESQL and _pg_pool:
        _pg_pool.closeall()
        _pg_pool = None
        logger.info("✅ PostgreSQL connection pool closed")
