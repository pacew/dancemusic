import unittest
import sqlite3
import os
import tempfile
from datetime import datetime
from backend.app.models import init_db, Event, Tune

class TestModels(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        init_db(self.db_path)
        
    def tearDown(self):
        # Close the database and remove the temporary file
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_event_schema(self):
        """Test that Event schema has the required fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check that events table exists with correct columns
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        self.assertIn('id', column_names)
        self.assertIn('name', column_names)
        self.assertIn('description', column_names)
        self.assertIn('tune_ids', column_names)
        self.assertIn('created_at', column_names)
        self.assertIn('updated_at', column_names)
        self.assertIn('deleted_at', column_names)
        
        # Check that tune_ids is stored as TEXT (JSON)
        for col in columns:
            if col[1] == 'tune_ids':
                self.assertEqual(col[2], 'TEXT')
                break
        
        conn.close()
    
    def test_tune_schema(self):
        """Test that Tune schema has the required fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check that tunes table exists with correct columns
        cursor.execute("PRAGMA table_info(tunes)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        self.assertIn('id', column_names)
        self.assertIn('title', column_names)
        self.assertIn('artist', column_names)
        self.assertIn('media_hash', column_names)
        self.assertIn('created_at', column_names)
        self.assertIn('updated_at', column_names)
        self.assertIn('deleted_at', column_names)
        
        # Check that media_hash is stored as TEXT
        for col in columns:
            if col[1] == 'media_hash':
                self.assertEqual(col[2], 'TEXT')
                break
        
        conn.close()
    
    def test_event_crud_operations(self):
        """Test Event CRUD operations"""
        # Create an event
        event = Event(
            name="Test Event",
            description="A test event",
            tune_ids=[1, 2, 3]
        )
        event.save(self.db_path)
        
        # Verify event was saved
        self.assertIsNotNone(event.id)
        
        # Retrieve the event
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (event.id,))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "Test Event")
        self.assertEqual(row[2], "A test event")
        self.assertEqual(row[3], "[1, 2, 3]")  # JSON string
        
        # Update the event
        event.name = "Updated Event"
        event.save(self.db_path)
        
        # Verify update
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM events WHERE id = ?", (event.id,))
        row = cursor.fetchone()
        conn.close()
        
        self.assertEqual(row[0], "Updated Event")
        
        # Delete the event
        event.delete(self.db_path)
        
        # Verify deletion
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deleted_at FROM events WHERE id = ?", (event.id,))
        row = cursor.fetchone()
        conn.close()
        
        # Check that deleted_at is an integer (timestamp)
        self.assertIsInstance(row[0], int)
        self.assertGreater(row[0], 0)
    
    def test_tune_crud_operations(self):
        """Test Tune CRUD operations"""
        # Create a tune
        media_content = b"test media content"
        media_hash = Tune.calculate_media_hash(media_content)
        
        tune = Tune(
            title="Test Tune",
            artist="Test Artist",
            media_hash=media_hash
        )
        tune.save(self.db_path)
        
        # Verify tune was saved
        self.assertIsNotNone(tune.id)
        
        # Retrieve the tune
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tunes WHERE id = ?", (tune.id,))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "Test Tune")
        self.assertEqual(row[2], "Test Artist")
        self.assertEqual(row[3], media_hash)
        
        # Update the tune
        tune.title = "Updated Tune"
        tune.save(self.db_path)
        
        # Verify update
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM tunes WHERE id = ?", (tune.id,))
        row = cursor.fetchone()
        conn.close()
        
        self.assertEqual(row[0], "Updated Tune")
        
        # Delete the tune
        tune.delete(self.db_path)
        
        # Verify deletion
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deleted_at FROM tunes WHERE id = ?", (tune.id,))
        row = cursor.fetchone()
        conn.close()
        
        # Check that deleted_at is an integer (timestamp)
        self.assertIsInstance(row[0], int)
        self.assertGreater(row[0], 0)
    
    def test_media_hash_calculation(self):
        """Test media hash calculation"""
        media_content = b"test media content"
        
        # Calculate hash
        actual_hash = Tune.calculate_media_hash(media_content)
        
        # Verify it's a valid SHA-256 hash (64 hex characters)
        self.assertEqual(len(actual_hash), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in actual_hash))

if __name__ == '__main__':
    unittest.main()
