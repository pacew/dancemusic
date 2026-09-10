import hashlib
import os
from pathlib import Path
from typing import Optional, BinaryIO

class CAS:
    """Content-Addressable Storage for media blobs"""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def _get_path(self, digest: str) -> Path:
        """Get filesystem path for a given digest"""
        return self.storage_path / digest
    
    def save_blob(self, data: bytes) -> str:
        """Save a blob and return its SHA-256 digest"""
        digest = hashlib.sha256(data).hexdigest()
        path = self._get_path(digest)
        
        # Only save if it doesn't exist yet (immutable)
        if not path.exists():
            with open(path, 'wb') as f:
                f.write(data)
        
        return digest
    
    def save_blob_from_file(self, file_path: str) -> str:
        """Save a blob from a file and return its SHA-256 digest"""
        with open(file_path, 'rb') as f:
            return self.save_blob(f.read())
    
    def get_blob(self, digest: str) -> Optional[bytes]:
        """Retrieve a blob by its digest"""
        path = self._get_path(digest)
        if not path.exists():
            return None
        return path.read_bytes()
    
    def get_blob_stream(self, digest: str) -> Optional[BinaryIO]:
        """Get a file stream for a blob by its digest"""
        path = self._get_path(digest)
        if not path.exists():
            return None
        return open(path, 'rb')
    
    def exists(self, digest: str) -> bool:
        """Check if a blob exists"""
        return self._get_path(digest).exists()
    
    def delete_blob(self, digest: str) -> bool:
        """Delete a blob by its digest"""
        path = self._get_path(digest)
        if path.exists():
            path.unlink()
            return True
        return False
