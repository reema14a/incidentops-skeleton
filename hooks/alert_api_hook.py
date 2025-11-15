def fetch_alerts():
    """Mocked alert source (simulating monitoring API)."""
    return [
        {"source": "DB", "type": "timeout", "message": "DB connection timeout"},
        {"source": "Server", "type": "threshold", "message": "Memory threshold exceeded"},
    ]
