import sqlite3
import uuid
from datetime import datetime

def init_db(filename=':memory:'):
    """Initialize the database with Events and Tunes tables"""
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    
    # Create Events table with UUID for setlists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            date TEXT,
            setlist_id TEXT UNIQUE,
            updated_at TEXT,
            deleted_at TEXT
        )
    ''')
    
    # Create Tunes table with CAS SHA-256 media_hash
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tunes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT,
            media_hash TEXT UNIQUE,
            updated_at TEXT,
            deleted_at TEXT
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_events_setlist_id ON events(setlist_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tunes_media_hash ON tunes(media_hash)
    ''')
    
    conn.commit()
    return conn

def create_event(conn, name, date, setlist_id=None):
    """Create a new event"""
    event_id = str(uuid.uuid4())
    if setlist_id is None:
        setlist_id = str(uuid.uuid4())
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (id, name, date, setlist_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (event_id, name, date, setlist_id, datetime.now().isoformat()))
    
    conn.commit()
    return event_id

def create_tune(conn, title, artist, media_hash):
    """Create a new tune"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tunes (title, artist, media_hash, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (title, artist, media_hash, datetime.now().isoformat()))
    
    conn.commit()
    return cursor.lastrowid

def mark_event_deleted(conn, event_id):
    """Mark an event as deleted"""
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE events 
        SET deleted_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), event_id))
    
    conn.commit()

def mark_tune_deleted(conn, tune_id):
    """Mark a tune as deleted"""
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tunes 
        SET deleted_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), tune_id))
    
    conn.commit()
