def test_import_backend_app():
    """Test that we can import backend.app"""
    try:
        import backend.app
        assert True
    except ImportError as e:
        assert False, f"Failed to import backend.app: {e}"
