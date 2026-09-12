import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
import time

# Database initialization
def init_db(db_path: str = "backend.db"):
    """Initialize the database with required tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            tune_ids TEXT NOT NULL,  -- JSON array of tune IDs
            created_at INTEGER DEFAULT (CAST((julianday('now') - 2440587.5) * 86400000 AS INTEGER)),
            updated_at INTEGER DEFAULT (CAST((julianday('now') - 2440587.5) * 86400000 AS INTEGER)),
            deleted_at INTEGER NULL
        )
    ''')
    
    # Create Tunes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tunes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT,
            media_hash TEXT NOT NULL,  -- SHA-256 hash of media content
            created_at INTEGER DEFAULT (CAST((julianday('now') - 2440587.5) * 86400000 AS INTEGER)),
            updated_at INTEGER DEFAULT (CAST((julianday('now') - 2440587.5) * 86400000 AS INTEGER)),
            deleted_at INTEGER NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Event model
class Event:
    def __init__(self, id: Optional[int] = None, name: str = "", description: str = "", 
                 tune_ids: List[int] = None, created_at: Optional[int] = None,
                 updated_at: Optional[int] = None, deleted_at: Optional[int] = None):
        self.id = id
        self.name = name
        self.description = description
        self.tune_ids = tune_ids or []
        self.created_at = created_at or int(datetime.now(timezone.utc).timestamp() * 1000)
        self.updated_at = updated_at or int(datetime.now(timezone.utc).timestamp() * 1000)
        self.deleted_at = deleted_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tune_ids': self.tune_ids,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deleted_at': self.deleted_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            tune_ids=json.loads(data.get('tune_ids', '[]')),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            deleted_at=data.get('deleted_at')
        )
    
    def save(self, db_path: str = "backend.db"):
        """Save the event to database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.id is None:
            # Insert new event
            cursor.execute('''
                INSERT INTO events (name, description, tune_ids, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.name, self.description, json.dumps(self.tune_ids), self.updated_at, self.deleted_at))
            self.id = cursor.lastrowid
        else:
            # Update existing event
            cursor.execute('''
                UPDATE events 
                SET name = ?, description = ?, tune_ids = ?, updated_at = ?, deleted_at = ?
                WHERE id = ?
            ''', (self.name, self.description, json.dumps(self.tune_ids), self.updated_at, self.deleted_at, self.id))
        
        conn.commit()
        conn.close()
    
    def delete(self, db_path: str = "backend.db"):
        """Mark event as deleted"""
        self.deleted_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.save(db_path)

# Tune model
class Tune:
    def __init__(self, id: Optional[int] = None, title: str = "", artist: str = "", 
                 media_hash: str = "", created_at: Optional[int] = None,
                 updated_at: Optional[int] = None, deleted_at: Optional[int] = None):
        self.id = id
        self.title = title
        self.artist = artist
        self.media_hash = media_hash
        self.created_at = created_at or int(datetime.now(timezone.utc).timestamp() * 1000)
        self.updated_at = updated_at or int(datetime.now(timezone.utc).timestamp() * 1000)
        self.deleted_at = deleted_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'media_hash': self.media_hash,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deleted_at': self.deleted_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            artist=data.get('artist', ''),
            media_hash=data.get('media_hash', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            deleted_at=data.get('deleted_at')
        )
    
    def save(self, db_path: str = "backend.db"):
        """Save the tune to database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.id is None:
            # Insert new tune
            cursor.execute('''
                INSERT INTO tunes (title, artist, media_hash, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.title, self.artist, self.media_hash, self.updated_at, self.deleted_at))
            self.id = cursor.lastrowid
        else:
            # Update existing tune
            cursor.execute('''
                UPDATE tunes 
                SET title = ?, artist = ?, media_hash = ?, updated_at = ?, deleted_at = ?
                WHERE id = ?
            ''', (self.title, self.artist, self.media_hash, self.updated_at, self.deleted_at, self.id))
        
        conn.commit()
        conn.close()
    
    def delete(self, db_path: str = "backend.db"):
        """Mark tune as deleted"""
        self.deleted_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.save(db_path)
    
    @staticmethod
    def calculate_media_hash(media_content: bytes) -> str:
        """Calculate SHA-256 hash of media content"""
        return hashlib.sha256(media_content).hexdigest()
