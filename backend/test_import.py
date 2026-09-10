def test_import_backend_app():
    """Test that we can import backend.app"""
    try:
        import backend.app
        assert backend.app is not None
    except ImportError as e:
        pytest.fail(f"Failed to import backend.app: {e}")
