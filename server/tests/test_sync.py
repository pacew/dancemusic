import unittest
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add parent directory to Python path so we can import sync module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from sync import get_state
from db import init_db

class TestSync(unittest.TestCase):
    def setUp(self):
        self.db_conn = init_db()
        
    def tearDown(self):
        # Clean up database after each test
        pass
        
    def test_get_state(self):
        """Test getting synchronization state"""
        result = get_state()
        self.assertIn('last_updated', result)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'synchronized')

if __name__ == '__main__':
    unittest.main()
