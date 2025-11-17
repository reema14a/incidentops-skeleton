"""
Unit tests for Pipeline Runner page logic.

Tests the core functionality without requiring Streamlit runtime.
"""
import pytest
import tempfile
import os
from orchestrator.orchestrator import PipelineExecutor
from agents.monitor_agent import MonitorAgent


def test_monitor_agent_with_custom_log_path():
    """Test that MonitorAgent can read from a custom log file path."""
    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write("2024-01-15 10:30:00 ERROR Database connection failed\n")
        tmp_file.write("2024-01-15 10:31:00 WARNING High memory usage detected\n")
        tmp_file_path = tmp_file.name
    
    try:
        # Create MonitorAgent with custom path
        monitor = MonitorAgent("TestMonitor", log_path=tmp_file_path)
        
        # Run the agent
        alerts = monitor.run()
        
        # Verify alerts were detected
        assert len(alerts) == 2
        assert alerts[0]['level'] == 'ERROR'
        assert alerts[1]['level'] == 'WARNING'
        assert 'Database connection failed' in alerts[0]['message']
        assert 'High memory usage detected' in alerts[1]['message']
        
    finally:
        # Clean up
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


def test_pipeline_executor_with_custom_monitor():
    """Test that PipelineExecutor can use a custom MonitorAgent."""
    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write("2024-01-15 10:30:00 ERROR Test error message\n")
        tmp_file_path = tmp_file.name
    
    try:
        # Create executor and replace MonitorAgent
        executor = PipelineExecutor()
        executor.agents['monitor'] = MonitorAgent("CustomMonitor", log_path=tmp_file_path)
        
        # Verify the custom monitor is set
        assert executor.agents['monitor'].log_path == tmp_file_path
        
    finally:
        # Clean up
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


def test_empty_log_input():
    """Test handling of empty log input."""
    # Create an empty temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write("")
        tmp_file_path = tmp_file.name
    
    try:
        # Create MonitorAgent with empty file
        monitor = MonitorAgent("TestMonitor", log_path=tmp_file_path)
        
        # Run the agent
        alerts = monitor.run()
        
        # Verify no alerts were detected
        assert len(alerts) == 0
        
    finally:
        # Clean up
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


def test_log_input_with_multiple_errors():
    """Test handling of log input with multiple error types."""
    # Create a temporary log file with various log levels
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write("2024-01-15 10:30:00 ERROR First error\n")
        tmp_file.write("2024-01-15 10:31:00 INFO Normal operation\n")
        tmp_file.write("2024-01-15 10:32:00 ERROR Second error\n")
        tmp_file.write("2024-01-15 10:33:00 WARNING Warning message\n")
        tmp_file.write("2024-01-15 10:34:00 DEBUG Debug info\n")
        tmp_file_path = tmp_file.name
    
    try:
        # Create MonitorAgent
        monitor = MonitorAgent("TestMonitor", log_path=tmp_file_path)
        
        # Run the agent
        alerts = monitor.run()
        
        # Verify only ERROR and WARNING alerts were detected
        assert len(alerts) == 3
        
        error_alerts = [a for a in alerts if a['level'] == 'ERROR']
        warning_alerts = [a for a in alerts if a['level'] == 'WARNING']
        
        assert len(error_alerts) == 2
        assert len(warning_alerts) == 1
        
    finally:
        # Clean up
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
