"""Unit tests for Local MCP Server router.

Tests the routing logic that maps tool names to implementations.
"""

import pytest
from unittest.mock import patch, MagicMock
from llm.local_mcp.router import route_tool_call


class TestRouteToolCall:
    """Test cases for route_tool_call function."""
    
    @patch('llm.local_mcp.tools.gmail_tool.gmail_send')
    def test_route_gmail_send(self, mock_gmail_send: MagicMock) -> None:
        """Test routing to gmail.send tool."""
        # Arrange
        mock_gmail_send.return_value = {
            "success": True,
            "message": "Email sent"
        }
        arguments = {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        # Act
        result = route_tool_call('gmail.send', arguments)
        
        # Assert
        mock_gmail_send.assert_called_once_with(arguments, None)
        assert result["success"] is True
        assert result["message"] == "Email sent"
    
    @patch('llm.local_mcp.tools.pushover_tool.pushover_send')
    def test_route_pushover_send(self, mock_pushover_send: MagicMock) -> None:
        """Test routing to pushover.send tool."""
        # Arrange
        mock_pushover_send.return_value = {
            "success": True,
            "message": "Notification sent"
        }
        arguments = {
            "user": "user123",
            "message": "Test notification",
            "title": "Test",
            "priority": 0
        }
        
        # Act
        result = route_tool_call('pushover.send', arguments)
        
        # Assert
        mock_pushover_send.assert_called_once_with(arguments, None)
        assert result["success"] is True
        assert result["message"] == "Notification sent"
    
    def test_route_unknown_tool(self) -> None:
        """Test routing with unknown tool name raises ValueError."""
        # Arrange
        arguments = {"test": "data"}
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            route_tool_call('unknown.tool', arguments)
        
        assert "Unknown tool" in str(exc_info.value)
        assert "unknown.tool" in str(exc_info.value)
    
    def test_route_empty_tool_name(self) -> None:
        """Test routing with empty tool name raises ValueError."""
        # Arrange
        arguments = {"test": "data"}
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            route_tool_call('', arguments)
        
        assert "Unknown tool" in str(exc_info.value)
