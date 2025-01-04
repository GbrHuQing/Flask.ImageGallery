import sqlite3
import hashlib
import secrets
from contextlib import contextmanager

DATABASE_NAME = 'users.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode(), 
        salt.encode(), 
        100000
    )
    return salt, hash_obj.hex()

def add_user(username: str, password: str) -> None:
    salt, hashed_password = hash_password(password)
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO users (username, password, salt) VALUES (?, ?, ?)',
            (username, hashed_password, salt)
        )
        conn.commit()

def user_exists(username: str) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        return c.fetchone() is not None

def verify_user(username: str, password: str) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT password, salt FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        
        if not result:
            return False
            
        stored_password, salt = result
        _, hashed_password = hash_password(password, salt)
        return stored_password == hashed_password 

def get_user_count() -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users')
        return c.fetchone()[0] 