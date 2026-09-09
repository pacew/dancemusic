import unittest
import os
import sys
import tempfile
import shutil

# Add the parent directory to the path so we can import db
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import init_db, create_event, create_tune, update_event, update_tune, soft_delete_event, soft_delete_tune, get_db_connection

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_database.db')
        
        # Patch the database path
        import db
        original_connect = db.sqlite3.connect
        
        def patched_connect(path, *args, **kwargs):
            if path == 'database.db':
                return original_connect(self.db_path, *args, **kwargs)
            return original_connect(path, *args, **kwargs)
        
        db.sqlite3.connect = patched_connect
        
        # Initialize database for testing
        init_db()
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    def test_create_event(self):
        """Test creating an event with UUID setlist"""
        event_id = create_event("Test Event", "2023-01-01", "setlist123")
        
        # Verify event was created
        conn = get_db_connection()
        event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        conn.close()
        
        self.assertIsNotNone(event)
        self.assertEqual(event['name'], "Test Event")
        self.assertEqual(event['date'], "2023-01-01")
        self.assertEqual(event['setlist'], "setlist123")
        self.assertIsNotNone(event['updated_at'])
        self.assertIsNone(event['deleted_at'])
        
    def test_create_tune(self):
        """Test creating a tune with SHA-256 media_hash"""
        media_hash = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        create_tune("Test Song", "Test Artist", media_hash)
        
        # Verify tune was created
        conn = get_db_connection()
        tune = conn.execute('SELECT * FROM tunes WHERE media_hash = ?', (media_hash,)).fetchone()
        conn.close()
        
        self.assertIsNotNone(tune)
        self.assertEqual(tune['title'], "Test Song")
        self.assertEqual(tune['artist'], "Test Artist")
        self.assertEqual(tune['media_hash'], media_hash)
        self.assertIsNotNone(tune['updated_at'])
        self.assertIsNone(tune['deleted_at'])
        
    def test_update_event(self):
        """Test updating an event"""
        event_id = create_event("Test Event", "2023-01-01", "setlist123")
        update_event(event_id, name="Updated Event", date="2023-01-02")
        
        # Verify event was updated
        conn = get_db_connection()
        event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        conn.close()
        
        self.assertEqual(event['name'], "Updated Event")
        self.assertEqual(event['date'], "2023-01-02")
        self.assertIsNotNone(event['updated_at'])
        
    def test_update_tune(self):
        """Test updating a tune"""
        media_hash = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        create_tune("Test Song", "Test Artist", media_hash)
        update_tune(1, title="Updated Song", artist="Updated Artist")
        
        # Verify tune was updated
        conn = get_db_connection()
        tune = conn.execute('SELECT * FROM tunes WHERE id = ?', (1,)).fetchone()
        conn.close()
        
        self.assertEqual(tune['title'], "Updated Song")
        self.assertEqual(tune['artist'], "Updated Artist")
        self.assertIsNotNone(tune['updated_at'])
        
    def test_soft_delete_event(self):
        """Test soft deleting an event"""
        event_id = create_event("Test Event", "2023-01-01", "setlist123")
        soft_delete_event(event_id)
        
        # Verify event was soft deleted
        conn = get_db_connection()
        event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        conn.close()
        
        self.assertIsNotNone(event['deleted_at'])
        
    def test_soft_delete_tune(self):
        """Test soft deleting a tune"""
        media_hash = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        create_tune("Test Song", "Test Artist", media_hash)
        soft_delete_tune(1)
        
        # Verify tune was soft deleted
        conn = get_db_connection()
        tune = conn.execute('SELECT * FROM tunes WHERE id = ?', (1,)).fetchone()
        conn.close()
        
        self.assertIsNotNone(tune['deleted_at'])

if __name__ == '__main__':
    unittest.main()
