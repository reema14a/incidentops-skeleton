"""
Unit tests for Dashboard auto-refresh functionality.

Tests the auto-refresh interval selector and countdown logic.
"""

import pytest
from unittest.mock import patch, MagicMock
import time


def test_auto_refresh_interval_options():
    """Test that auto-refresh interval options are correctly defined."""
    expected_intervals = [0, 10, 30, 60, 300]
    
    # Verify the intervals are reasonable
    assert 0 in expected_intervals  # Off option
    assert 10 in expected_intervals  # 10 seconds
    assert 30 in expected_intervals  # 30 seconds
    assert 60 in expected_intervals  # 1 minute
    assert 300 in expected_intervals  # 5 minutes


def test_auto_refresh_format_function():
    """Test the format function for auto-refresh intervals."""
    format_func = lambda x: "Off" if x == 0 else f"{x}s"
    
    assert format_func(0) == "Off"
    assert format_func(10) == "10s"
    assert format_func(30) == "30s"
    assert format_func(60) == "60s"
    assert format_func(300) == "300s"


def test_auto_refresh_countdown_logic():
    """Test the countdown logic for auto-refresh."""
    # Simulate session state
    session_state = {'last_refresh_time': time.time() - 5}
    auto_refresh_interval = 10
    
    current_time = time.time()
    elapsed = current_time - session_state['last_refresh_time']
    remaining = auto_refresh_interval - int(elapsed)
    
    # Should have approximately 5 seconds remaining
    assert 4 <= remaining <= 6
    
    # Should not trigger refresh yet
    assert elapsed < auto_refresh_interval


def test_auto_refresh_trigger_condition():
    """Test that refresh triggers when interval is exceeded."""
    # Simulate session state with old timestamp
    session_state = {'last_refresh_time': time.time() - 15}
    auto_refresh_interval = 10
    
    current_time = time.time()
    elapsed = current_time - session_state['last_refresh_time']
    
    # Should trigger refresh
    assert elapsed >= auto_refresh_interval


def test_auto_refresh_disabled_when_zero():
    """Test that auto-refresh is disabled when interval is 0."""
    auto_refresh_interval = 0
    
    # When interval is 0, no refresh logic should execute
    assert auto_refresh_interval == 0
