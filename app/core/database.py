import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import get_settings

settings = get_settings()

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        yield conn
    finally:
        if conn is not None:
            conn.close()

@contextmanager
def get_db_cursor():
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

def init_db():
    """Initialize database tables"""
    with get_db_cursor() as cursor:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_audit (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                action VARCHAR(50) NOT NULL,
                changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                changed_by VARCHAR(100),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create index on user_id and version for faster audit queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_audit_user_id_version 
            ON user_audit(user_id, version)
        """)
