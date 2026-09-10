import unittest
import tempfile
import os
from pathlib import Path

# Add the server directory to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cas import CAS

class TestCAS(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cas = CAS(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_save_and_retrieve_blob(self):
        """Test saving and retrieving a blob"""
        data = b"Hello, World!"
        digest = self.cas.save_blob(data)
        
        # Verify the digest is correct
        expected_digest = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(digest, expected_digest)
        
        # Verify we can retrieve the blob
        retrieved = self.cas.get_blob(digest)
        self.assertEqual(retrieved, data)
    
    def test_save_blob_from_file(self):
        """Test saving a blob from a file"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Test file content")
            temp_file_path = f.name
        
        try:
            digest = self.cas.save_blob_from_file(temp_file_path)
            retrieved = self.cas.get_blob(digest)
            self.assertEqual(retrieved, b"Test file content")
        finally:
            os.unlink(temp_file_path)
    
    def test_blob_exists(self):
        """Test checking if a blob exists"""
        data = b"Test data"
        digest = self.cas.save_blob(data)
        
        # Should exist
        self.assertTrue(self.cas.exists(digest))
        
        # Should not exist for non-existent digest
        self.assertFalse(self.cas.exists("nonexistent"))
    
    def test_get_blob_stream(self):
        """Test getting a blob as a stream"""
        data = b"Stream test data"
        digest = self.cas.save_blob(data)
        
        stream = self.cas.get_blob_stream(digest)
        self.assertIsNotNone(stream)
        
        # Read from stream
        content = stream.read()
        stream.close()
        self.assertEqual(content, data)
    
    def test_delete_blob(self):
        """Test deleting a blob"""
        data = b"Delete test"
        digest = self.cas.save_blob(data)
        
        # Should exist before deletion
        self.assertTrue(self.cas.exists(digest))
        
        # Delete it
        result = self.cas.delete_blob(digest)
        self.assertTrue(result)
        
        # Should not exist after deletion
        self.assertFalse(self.cas.exists(digest))
        
        # Deleting non-existent blob should return False
        result = self.cas.delete_blob("nonexistent")
        self.assertFalse(result)
    
    def test_immutable_storage(self):
        """Test that blobs are immutable (same data produces same digest)"""
        data1 = b"Same content"
        data2 = b"Same content"
        
        digest1 = self.cas.save_blob(data1)
        digest2 = self.cas.save_blob(data2)
        
        # Same content should produce same digest
        self.assertEqual(digest1, digest2)
        
        # Try to save same content again - should not create new file
        digest3 = self.cas.save_blob(data1)
        self.assertEqual(digest1, digest3)
        
        # Verify content is still correct
        retrieved = self.cas.get_blob(digest1)
        self.assertEqual(retrieved, data1)

if __name__ == '__main__':
    unittest.main()
