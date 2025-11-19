"""Unit tests for Pushover tool.

Tests the pushover.send tool implementation with mocked API.
"""

import pytest
from unittest.mock import patch, MagicMock
from llm.local_mcp.tools.pushover_tool import pushover_send


class TestPushoverSend:
    """Test cases for pushover_send function."""
    
    @patch('llm.local_mcp.tools.pushover_tool.requests.post')
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_pushover_send_success(self, mock_get_settings: MagicMock, mock_post: MagicMock) -> None:
        """Test successful push notification sending."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = 'test_api_token'
        mock_get_settings.return_value = mock_settings
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 1,
            'request': 'test_request_id'
        }
        mock_post.return_value = mock_response
        
        arguments = {
            "user": "user_key_123",
            "message": "Test notification message",
            "title": "Test Title",
            "priority": 1
        }
        
        # Act
        result = pushover_send(arguments)
        
        # Assert
        assert result["success"] is True
        assert result["request_id"] == "test_request_id"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['data']['token'] == 'test_api_token'
        assert call_args[1]['data']['user'] == 'user_key_123'
        assert call_args[1]['data']['message'] == 'Test notification message'
    
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_pushover_send_missing_token(self, mock_get_settings: MagicMock) -> None:
        """Test error when Pushover API token is missing."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = None
        mock_get_settings.return_value = mock_settings
        
        arguments = {
            "user": "user_key_123",
            "message": "Test message"
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            pushover_send(arguments)
        
        assert "Missing required argument: token" in str(exc_info.value)
    
    def test_pushover_send_missing_required_field(self) -> None:
        """Test error when required field is missing."""
        # Arrange
        arguments = {
            "user": "user_key_123"
            # Missing 'message'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            pushover_send(arguments)
        
        assert "Missing required argument: message" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.pushover_tool.requests.post')
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_pushover_send_api_error(self, mock_get_settings: MagicMock, mock_post: MagicMock) -> None:
        """Test error when Pushover API returns error response."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = 'test_api_token'
        mock_get_settings.return_value = mock_settings
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.json.return_value = {
            'status': 0,
            'errors': ['user identifier is invalid']
        }
        mock_post.return_value = mock_response
        
        arguments = {
            "user": "invalid_user",
            "message": "Test message"
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            pushover_send(arguments)
        
        assert "Pushover API request failed with status 400" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.pushover_tool.requests.post')
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_pushover_send_network_error(self, mock_get_settings: MagicMock, mock_post: MagicMock) -> None:
        """Test error when network request fails."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = 'test_api_token'
        mock_get_settings.return_value = mock_settings
        
        # Mock network error
        mock_post.side_effect = Exception("Network unreachable")
        
        arguments = {
            "user": "user_key_123",
            "message": "Test message"
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            pushover_send(arguments)
        
        assert "Network unreachable" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.pushover_tool.requests.post')
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_pushover_send_timeout_error(self, mock_get_settings: MagicMock, mock_post: MagicMock) -> None:
        """Test error when API request times out."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = 'test_api_token'
        mock_get_settings.return_value = mock_settings
        
        # Mock timeout error
        import requests
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        arguments = {
            "user": "user_key_123",
            "message": "Test message"
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            pushover_send(arguments)
        
        assert "Pushover API request timed out" in str(exc_info.value)
    
    def test_pushover_send_missing_user_field(self) -> None:
        """Test error when 'user' field is missing."""
        # Arrange
        arguments = {
            "message": "Test message"
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            pushover_send(arguments)
        
        assert "Missing required argument: user" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.pushover_tool.requests.post')
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_pushover_send_with_optional_fields(self, mock_get_settings: MagicMock, mock_post: MagicMock) -> None:
        """Test successful send with optional title and priority fields."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = 'test_api_token'
        mock_get_settings.return_value = mock_settings
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 1,
            'request': 'test_request_id'
        }
        mock_post.return_value = mock_response
        
        arguments = {
            "user": "user_key_123",
            "message": "Test notification message",
            "title": "Test Title",
            "priority": 2
        }
        
        # Act
        result = pushover_send(arguments)
        
        # Assert
        assert result["success"] is True
        mock_post.assert_called_once()
        call_data = mock_post.call_args[1]['data']
        assert call_data['user'] == 'user_key_123'
        assert call_data['message'] == 'Test notification message'
        assert call_data['title'] == 'Test Title'
        assert call_data['priority'] == 2
