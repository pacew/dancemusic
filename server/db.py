import sqlite3
import uuid
from datetime import datetime

def init_db():
    """Initialize the database with Events and Tunes tables"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create Events table with UUID for setlists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            date TEXT,
            setlist TEXT,
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
            media_hash TEXT UNIQUE NOT NULL,
            updated_at TEXT,
            deleted_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_event(name, date, setlist):
    """Create a new event"""
    conn = get_db_connection()
    event_id = str(uuid.uuid4())
    
    conn.execute('''
        INSERT INTO events (id, name, date, setlist, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (event_id, name, date, setlist, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return event_id

def create_tune(title, artist, media_hash):
    """Create a new tune"""
    conn = get_db_connection()
    
    conn.execute('''
        INSERT INTO tunes (title, artist, media_hash, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (title, artist, media_hash, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def update_event(event_id, name=None, date=None, setlist=None):
    """Update an existing event"""
    conn = get_db_connection()
    
    # Build dynamic update query
    updates = []
    values = []
    
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if date is not None:
        updates.append("date = ?")
        values.append(date)
    if setlist is not None:
        updates.append("setlist = ?")
        values.append(setlist)
    
    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(event_id)
    
    if updates:
        query = f"UPDATE events SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
    
    conn.close()

def update_tune(tune_id, title=None, artist=None, media_hash=None):
    """Update an existing tune"""
    conn = get_db_connection()
    
    # Build dynamic update query
    updates = []
    values = []
    
    if title is not None:
        updates.append("title = ?")
        values.append(title)
    if artist is not None:
        updates.append("artist = ?")
        values.append(artist)
    if media_hash is not None:
        updates.append("media_hash = ?")
        values.append(media_hash)
    
    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(tune_id)
    
    if updates:
        query = f"UPDATE tunes SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
    
    conn.close()

def soft_delete_event(event_id):
    """Soft delete an event by setting deleted_at"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE events 
        SET deleted_at = ? 
        WHERE id = ?
    ''', (datetime.now().isoformat(), event_id))
    conn.commit()
    conn.close()

def soft_delete_tune(tune_id):
    """Soft delete a tune by setting deleted_at"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE tunes 
        SET deleted_at = ? 
        WHERE id = ?
    ''', (datetime.now().isoformat(), tune_id))
    conn.commit()
    conn.close()

# Initialize the database
if __name__ == "__main__":
    init_db()
