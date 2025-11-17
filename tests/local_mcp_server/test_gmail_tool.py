"""Unit tests for Gmail tool.

Tests the gmail.send tool implementation with mocked SMTP.
"""

import pytest
from unittest.mock import patch, MagicMock
from llm.local_mcp.tools.gmail_tool import gmail_send


class TestGmailSend:
    """Test cases for gmail_send function."""
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_gmail_send_success(self, mock_get_settings: MagicMock, mock_smtp: MagicMock) -> None:
        """Test successful email sending."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        arguments = {
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test body content"
        }
        
        # Act
        result = gmail_send(arguments)
        
        # Assert
        assert result["success"] is True
        assert result["recipient"] == "recipient@example.com"
        assert result["subject"] == "Test Subject"
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@gmail.com', 'test_password')
        mock_server.sendmail.assert_called_once()
    
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_gmail_send_missing_credentials(self, mock_get_settings: MagicMock) -> None:
        """Test error when Gmail credentials are missing."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = None
        mock_get_settings.return_value = mock_settings
        
        arguments = {
            "to": "recipient@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            gmail_send(arguments)
        
        assert "Gmail credentials not configured" in str(exc_info.value)
    
    def test_gmail_send_missing_required_field(self) -> None:
        """Test error when required field is missing."""
        # Arrange
        arguments = {
            "to": "recipient@example.com",
            "subject": "Test"
            # Missing 'body'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            gmail_send(arguments)
        
        assert "Missing required argument: body" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_gmail_send_smtp_connection_error(self, mock_get_settings: MagicMock, mock_smtp: MagicMock) -> None:
        """Test error when SMTP connection fails."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        # Mock SMTP to raise connection error
        mock_smtp.side_effect = Exception("Connection refused")
        
        arguments = {
            "to": "recipient@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            gmail_send(arguments)
        
        assert "Connection refused" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_gmail_send_authentication_error(self, mock_get_settings: MagicMock, mock_smtp: MagicMock) -> None:
        """Test error when SMTP authentication fails."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'wrong_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        arguments = {
            "to": "recipient@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            gmail_send(arguments)
        
        assert "Authentication failed" in str(exc_info.value)
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_gmail_send_sendmail_error(self, mock_get_settings: MagicMock, mock_smtp: MagicMock) -> None:
        """Test error when sendmail operation fails."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = Exception("Recipient rejected")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        arguments = {
            "to": "invalid@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            gmail_send(arguments)
        
        assert "Recipient rejected" in str(exc_info.value)
    
    def test_gmail_send_missing_to_field(self) -> None:
        """Test error when 'to' field is missing."""
        # Arrange
        arguments = {
            "subject": "Test",
            "body": "Test body"
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            gmail_send(arguments)
        
        assert "Missing required argument: to" in str(exc_info.value)
    
    def test_gmail_send_missing_subject_field(self) -> None:
        """Test error when 'subject' field is missing."""
        # Arrange
        arguments = {
            "to": "recipient@example.com",
            "body": "Test body"
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            gmail_send(arguments)
        
        assert "Missing required argument: subject" in str(exc_info.value)
