"""Local MCP Server for IncidentOps.

A minimal HTTP-based MCP server that exposes notification tools
(gmail.send and pushover.send) via JSON-RPC 2.0 protocol.

This server replaces the complex viaSocket/SSE/WebSocket infrastructure
with a simple local HTTP endpoint.
"""

import logging
import json
import os
from typing import Any, Dict, Optional
from flask import Flask, request, jsonify
from logging.handlers import RotatingFileHandler

# Configure logging to both console and file
def setup_logging() -> logging.Logger:
    """Configure logging for MCP server with console and file handlers.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("LocalMCPServer")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Format for log messages
    log_format = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'mcp_server.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)


def _redact_secrets(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive information from arguments for safe logging.
    
    Args:
        arguments: Tool arguments that may contain secrets.
        
    Returns:
        dict: Arguments with secrets redacted.
    """
    # List of field names that should be redacted
    secret_fields = {
        'password', 'token', 'api_key', 'secret', 'key',
        'user_key', 'app_password', 'credentials'
    }
    
    safe_args = {}
    for key, value in arguments.items():
        # Check if field name suggests it contains a secret
        if any(secret in key.lower() for secret in secret_fields):
            safe_args[key] = '[REDACTED]'
        else:
            safe_args[key] = value
    
    return safe_args


class JSONRPCError:
    """JSON-RPC 2.0 error codes and messages."""
    
    PARSE_ERROR = (-32700, "Parse error")
    INVALID_REQUEST = (-32600, "Invalid Request")
    METHOD_NOT_FOUND = (-32601, "Method not found")
    INVALID_PARAMS = (-32602, "Invalid params")
    INTERNAL_ERROR = (-32603, "Internal error")
    
    @staticmethod
    def create_error_response(
        request_id: Optional[Any],
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Create a JSON-RPC 2.0 error response.
        
        Args:
            request_id: The request ID (can be None for parse errors).
            code: Error code.
            message: Error message.
            data: Optional additional error data.
            
        Returns:
            dict: JSON-RPC error response.
        """
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        
        if data is not None:
            error_response["error"]["data"] = data
        
        return error_response


def create_success_response(request_id: Any, result: Any) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 success response.
    
    Args:
        request_id: The request ID.
        result: The result data.
        
    Returns:
        dict: JSON-RPC success response.
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


@app.route('/send', methods=['POST'])
def handle_send() -> Any:
    """Handle JSON-RPC 2.0 requests on POST /send endpoint.
    
    Accepts JSON-RPC 2.0 requests with method = "tools/call".
    Routes to appropriate tool implementation based on params.name.
    
    Returns:
        JSON response: JSON-RPC 2.0 compliant response.
    """
    # Parse JSON request
    try:
        rpc_request = request.get_json(force=True)
    except Exception as e:
        logger.error(f"Failed to parse JSON request: {e}")
        return jsonify(JSONRPCError.create_error_response(
            None,
            *JSONRPCError.PARSE_ERROR,
            data=str(e)
        )), 400
    
    # Validate JSON-RPC structure
    if not isinstance(rpc_request, dict):
        logger.error("Request is not a JSON object")
        return jsonify(JSONRPCError.create_error_response(
            None,
            *JSONRPCError.INVALID_REQUEST,
            data="Request must be a JSON object"
        )), 400
    
    # Extract request ID (required for all responses except parse errors)
    request_id = rpc_request.get('id')
    
    # Validate jsonrpc version
    if rpc_request.get('jsonrpc') != '2.0':
        logger.error(f"Invalid jsonrpc version: {rpc_request.get('jsonrpc')}")
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.INVALID_REQUEST,
            data="jsonrpc must be '2.0'"
        )), 400
    
    # Validate method
    method = rpc_request.get('method')
    if method != 'tools/call':
        logger.error(f"Unsupported method: {method}")
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.METHOD_NOT_FOUND,
            data=f"Method '{method}' not supported. Use 'tools/call'."
        )), 400
    
    # Extract params
    params = rpc_request.get('params', {})
    if not isinstance(params, dict):
        logger.error("Params must be an object")
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.INVALID_PARAMS,
            data="params must be a JSON object"
        )), 400
    
    # Extract tool name
    tool_name = params.get('name')
    if not tool_name:
        logger.error("Missing tool name in params")
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.INVALID_PARAMS,
            data="params.name is required"
        )), 400
    
    # Extract tool arguments
    tool_arguments = params.get('arguments', {})
    
    # Redact secrets from arguments for logging
    safe_arguments = _redact_secrets(tool_arguments)
    
    # Log request start (without secrets)
    logger.info(
        f"[request_id={request_id}] [tool={tool_name}] [status=started] "
        f"Tool execution started with arguments: {safe_arguments}"
    )
    
    # Route to tool implementation
    try:
        from llm.local_mcp.router import route_tool_call
        
        result = route_tool_call(tool_name, tool_arguments, request_id)
        
        logger.info(
            f"[request_id={request_id}] [tool={tool_name}] [status=success] "
            f"Tool execution completed successfully"
        )
        return jsonify(create_success_response(request_id, result)), 200
        
    except ImportError as e:
        logger.error(
            f"[request_id={request_id}] [tool={tool_name}] [status=failure] "
            f"Failed to import router: {e}",
            exc_info=True
        )
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.INTERNAL_ERROR,
            data="Router module not available"
        )), 500
    except ValueError as e:
        # Tool not found or invalid parameters
        logger.error(
            f"[request_id={request_id}] [tool={tool_name}] [status=failure] "
            f"Tool error: {e}",
            exc_info=True
        )
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.INVALID_PARAMS,
            data=str(e)
        )), 400
    except Exception as e:
        # Internal tool execution error
        logger.error(
            f"[request_id={request_id}] [tool={tool_name}] [status=failure] "
            f"Tool execution failed: {e}",
            exc_info=True
        )
        return jsonify(JSONRPCError.create_error_response(
            request_id,
            *JSONRPCError.INTERNAL_ERROR,
            data=str(e)
        )), 500


@app.route('/health', methods=['GET'])
def health_check() -> Any:
    """Health check endpoint.
    
    Returns:
        JSON response: Server status.
    """
    return jsonify({
        "status": "healthy",
        "server": "LocalMCPServer",
        "version": "1.0.0"
    }), 200


def run_server(host: str = '0.0.0.0', port: int = None, debug: bool = False):
    """Run the local MCP server.
    
    Args:
        host: Host address to bind to.
        port: Port number to listen on.
        debug: Enable Flask debug mode.
    """
    if port is None:
        port = int(os.environ.get("PORT", 5005))

    logger.info(f"Starting Local MCP Server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
