"""Integration tests for Local MCP Server JSON-RPC 2.0 compliance.

Tests that all server responses conform to JSON-RPC 2.0 specification:
- Success responses have: jsonrpc, id, result
- Error responses have: jsonrpc, id, error (with code, message, optional data)
- All error codes follow JSON-RPC 2.0 standard
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from llm.local_mcp.server import app, JSONRPCError


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestJSONRPCCompliance:
    """Test JSON-RPC 2.0 compliance for all response types."""
    
    def test_parse_error_response_structure(self, client) -> None:
        """Test that parse errors return valid JSON-RPC error response."""
        # Send invalid JSON
        response = client.post(
            '/send',
            data='invalid json{',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Validate JSON-RPC structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] is None  # Parse errors have null id
        assert 'error' in data
        assert data['error']['code'] == -32700
        assert 'Parse error' in data['error']['message']
        assert 'result' not in data  # Error responses must not have result
    
    def test_invalid_request_missing_jsonrpc(self, client) -> None:
        """Test invalid request when jsonrpc field is missing."""
        request_data = {
            'id': 1,
            'method': 'tools/call',
            'params': {}
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Validate JSON-RPC error structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 1
        assert 'error' in data
        assert data['error']['code'] == -32600
        assert 'Invalid Request' in data['error']['message']
        assert 'result' not in data
    
    def test_invalid_request_wrong_jsonrpc_version(self, client) -> None:
        """Test invalid request when jsonrpc version is not 2.0."""
        request_data = {
            'jsonrpc': '1.0',
            'id': 2,
            'method': 'tools/call',
            'params': {}
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 2
        assert data['error']['code'] == -32600
        assert 'result' not in data
    
    def test_method_not_found_response(self, client) -> None:
        """Test method not found error response."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'unknown/method',
            'params': {}
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Validate JSON-RPC error structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 3
        assert 'error' in data
        assert data['error']['code'] == -32601
        assert 'Method not found' in data['error']['message']
        assert 'result' not in data
    
    def test_invalid_params_missing_tool_name(self, client) -> None:
        """Test invalid params when tool name is missing."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 4,
            'method': 'tools/call',
            'params': {
                'arguments': {}
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Validate JSON-RPC error structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 4
        assert 'error' in data
        assert data['error']['code'] == -32602
        assert 'Invalid params' in data['error']['message']
        assert 'result' not in data
    
    def test_invalid_params_unknown_tool(self, client) -> None:
        """Test invalid params when tool is unknown."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 5,
            'method': 'tools/call',
            'params': {
                'name': 'unknown.tool',
                'arguments': {}
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Validate JSON-RPC error structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 5
        assert 'error' in data
        assert data['error']['code'] == -32602
        assert 'result' not in data
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_success_response_structure(self, mock_get_settings: MagicMock, mock_smtp: MagicMock, client) -> None:
        """Test that successful tool calls return valid JSON-RPC success response."""
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        request_data = {
            'jsonrpc': '2.0',
            'id': 6,
            'method': 'tools/call',
            'params': {
                'name': 'gmail.send',
                'arguments': {
                    'to': 'test@example.com',
                    'subject': 'Test',
                    'body': 'Test body'
                }
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Validate JSON-RPC success structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 6
        assert 'result' in data
        assert 'error' not in data  # Success responses must not have error
        
        # Validate result content
        assert data['result']['success'] is True
        assert 'message' in data['result']
    
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_internal_error_response(self, mock_get_settings: MagicMock, client) -> None:
        """Test internal error response when tool execution fails."""
        # Mock settings to return None (missing credentials)
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = None
        mock_get_settings.return_value = mock_settings
        
        request_data = {
            'jsonrpc': '2.0',
            'id': 7,
            'method': 'tools/call',
            'params': {
                'name': 'gmail.send',
                'arguments': {
                    'to': 'test@example.com',
                    'subject': 'Test',
                    'body': 'Test body'
                }
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Validate JSON-RPC error structure
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 7
        assert 'error' in data
        assert data['error']['code'] == -32602  # Invalid params for missing credentials
        assert 'result' not in data
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_tool_execution_exception_smtp_error(self, mock_get_settings: MagicMock, mock_smtp: MagicMock, client) -> None:
        """Test that SMTP exceptions during tool execution return internal error."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        request_data = {
            'jsonrpc': '2.0',
            'id': 12,
            'method': 'tools/call',
            'params': {
                'name': 'gmail.send',
                'arguments': {
                    'to': 'test@example.com',
                    'subject': 'Test',
                    'body': 'Test body'
                }
            }
        }
        
        # Act
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 500
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 12
        assert 'error' in data
        assert data['error']['code'] == -32603  # Internal error
        assert 'SMTP connection failed' in data['error']['data']
        assert 'result' not in data
    
    @patch('llm.local_mcp.tools.pushover_tool.requests.post')
    @patch('llm.local_mcp.tools.pushover_tool.get_settings')
    def test_tool_execution_exception_api_error(self, mock_get_settings: MagicMock, mock_post: MagicMock, client) -> None:
        """Test that API exceptions during tool execution return internal error."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.return_value = 'test_api_token'
        mock_get_settings.return_value = mock_settings
        
        # Mock API to raise exception
        mock_post.side_effect = Exception("API connection timeout")
        
        request_data = {
            'jsonrpc': '2.0',
            'id': 13,
            'method': 'tools/call',
            'params': {
                'name': 'pushover.send',
                'arguments': {
                    'user': 'user_key_123',
                    'message': 'Test message'
                }
            }
        }
        
        # Act
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 500
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 13
        assert 'error' in data
        assert data['error']['code'] == -32603  # Internal error
        assert 'API connection timeout' in data['error']['data']
        assert 'result' not in data
    
    @patch('llm.local_mcp.tools.gmail_tool.get_settings')
    def test_tool_missing_required_argument(self, mock_get_settings: MagicMock, client) -> None:
        """Test that missing required arguments return invalid params error."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@gmail.com',
            'GMAIL_PASSWORD': 'test_password'
        }.get(key)
        mock_get_settings.return_value = mock_settings
        
        request_data = {
            'jsonrpc': '2.0',
            'id': 14,
            'method': 'tools/call',
            'params': {
                'name': 'gmail.send',
                'arguments': {
                    'to': 'test@example.com',
                    'subject': 'Test'
                    # Missing 'body'
                }
            }
        }
        
        # Act
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 14
        assert 'error' in data
        assert data['error']['code'] == -32602  # Invalid params
        assert 'Missing required argument' in data['error']['data']
        assert 'result' not in data
    
    def test_request_with_string_id(self, client) -> None:
        """Test that string IDs are preserved in responses."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 'string-id-123',
            'method': 'unknown/method',
            'params': {}
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        # ID should be preserved exactly as sent
        assert data['id'] == 'string-id-123'
        assert data['jsonrpc'] == '2.0'
    
    def test_request_with_null_id(self, client) -> None:
        """Test that null IDs are preserved in responses."""
        request_data = {
            'jsonrpc': '2.0',
            'id': None,
            'method': 'unknown/method',
            'params': {}
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        # ID should be preserved as null
        assert data['id'] is None
        assert data['jsonrpc'] == '2.0'
    
    def test_request_not_json_object(self, client) -> None:
        """Test that non-object JSON returns invalid request error."""
        # Send JSON array instead of object
        response = client.post(
            '/send',
            data='["not", "an", "object"]',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] is None
        assert data['error']['code'] == -32600
        assert 'result' not in data
    
    def test_params_not_object(self, client) -> None:
        """Test that non-object params returns invalid params error."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 8,
            'method': 'tools/call',
            'params': ['not', 'an', 'object']
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 8
        assert data['error']['code'] == -32602
        assert 'result' not in data
    
    def test_missing_method_field(self, client) -> None:
        """Test invalid request when method field is missing."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 9,
            'params': {}
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 9
        assert data['error']['code'] == -32601
        assert 'result' not in data
    
    def test_missing_id_field(self, client) -> None:
        """Test that requests without id field are handled (notification)."""
        request_data = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': 'unknown.tool',
                'arguments': {}
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Response should still have jsonrpc and error
        assert data['jsonrpc'] == '2.0'
        assert 'id' in data  # id will be None
        assert data['error']['code'] == -32602
    
    def test_empty_tool_name(self, client) -> None:
        """Test invalid params when tool name is empty string."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 10,
            'method': 'tools/call',
            'params': {
                'name': '',
                'arguments': {}
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 10
        assert data['error']['code'] == -32602
        assert 'result' not in data
    
    def test_params_missing_arguments_field(self, client) -> None:
        """Test that missing arguments field defaults to empty dict."""
        request_data = {
            'jsonrpc': '2.0',
            'id': 11,
            'method': 'tools/call',
            'params': {
                'name': 'unknown.tool'
                # Missing 'arguments' field
            }
        }
        
        response = client.post(
            '/send',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # Should fail because tool doesn't exist, not because arguments is missing
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 11
        assert data['error']['code'] == -32602
        assert 'Unknown tool' in data['error']['data']


class TestJSONRPCErrorCodes:
    """Test that all error codes follow JSON-RPC 2.0 standard."""
    
    def test_error_code_constants(self) -> None:
        """Test that error code constants match JSON-RPC 2.0 spec."""
        assert JSONRPCError.PARSE_ERROR == (-32700, "Parse error")
        assert JSONRPCError.INVALID_REQUEST == (-32600, "Invalid Request")
        assert JSONRPCError.METHOD_NOT_FOUND == (-32601, "Method not found")
        assert JSONRPCError.INVALID_PARAMS == (-32602, "Invalid params")
        assert JSONRPCError.INTERNAL_ERROR == (-32603, "Internal error")
    
    def test_create_error_response_structure(self) -> None:
        """Test that create_error_response generates valid structure."""
        error_response = JSONRPCError.create_error_response(
            request_id=123,
            code=-32600,
            message="Test error",
            data="Additional info"
        )
        
        assert error_response['jsonrpc'] == '2.0'
        assert error_response['id'] == 123
        assert error_response['error']['code'] == -32600
        assert error_response['error']['message'] == "Test error"
        assert error_response['error']['data'] == "Additional info"
        assert 'result' not in error_response
    
    def test_create_error_response_without_data(self) -> None:
        """Test error response without optional data field."""
        error_response = JSONRPCError.create_error_response(
            request_id=456,
            code=-32601,
            message="Method not found"
        )
        
        assert error_response['jsonrpc'] == '2.0'
        assert error_response['id'] == 456
        assert error_response['error']['code'] == -32601
        assert error_response['error']['message'] == "Method not found"
        assert 'data' not in error_response['error']
