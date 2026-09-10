import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

import sqlite3
from datetime import datetime
from db import init_db, create_event, create_tune, mark_event_deleted, mark_tune_deleted

class TestDB(unittest.TestCase):
    def setUp(self):
        self.conn = init_db(':memory:')
    
    def tearDown(self):
        self.conn.close()
    
    def test_create_event_with_uuid_setlist(self):
        """Test that events use UUID for setlists"""
        event_id = create_event(self.conn, "Test Event", "2023-01-01")
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT setlist_id FROM events WHERE id = ?', (event_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        # Check that setlist_id is a valid UUID
        import uuid
        setlist_id = result[0]
        self.assertIsInstance(uuid.UUID(setlist_id), uuid.UUID)
    
    def test_create_tune_with_sha256_hash(self):
        """Test that tunes implement CAS SHA-256 media_hash"""
        media_hash = "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
        tune_id = create_tune(self.conn, "Test Tune", "Test Artist", media_hash)
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT media_hash FROM tunes WHERE id = ?', (tune_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], media_hash)
    
    def test_tombstone_fields_exist(self):
        """Test that both tables implement updated_at and deleted_at"""
        # Test events table
        event_id = create_event(self.conn, "Test Event", "2023-01-01")
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT updated_at, deleted_at FROM events WHERE id = ?', (event_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])  # updated_at should not be None
        self.assertIsNone(result[1])     # deleted_at should be None initially
        
        # Test tunes table
        media_hash = "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
        tune_id = create_tune(self.conn, "Test Tune", "Test Artist", media_hash)
        
        cursor.execute('SELECT updated_at, deleted_at FROM tunes WHERE id = ?', (tune_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])  # updated_at should not be None
        self.assertIsNone(result[1])     # deleted_at should be None initially
    
    def test_mark_event_deleted(self):
        """Test marking an event as deleted"""
        event_id = create_event(self.conn, "Test Event", "2023-01-01")
        mark_event_deleted(self.conn, event_id)
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT deleted_at FROM events WHERE id = ?', (event_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])  # deleted_at should not be None
    
    def test_mark_tune_deleted(self):
        """Test marking a tune as deleted"""
        media_hash = "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
        tune_id = create_tune(self.conn, "Test Tune", "Test Artist", media_hash)
        mark_tune_deleted(self.conn, tune_id)
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT deleted_at FROM tunes WHERE id = ?', (tune_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])  # deleted_at should not be None

if __name__ == '__main__':
    unittest.main()
