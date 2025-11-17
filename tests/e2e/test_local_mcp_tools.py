"""Demo script to test Local MCP Server tools.

This script demonstrates how to use the gmail.send and pushover.send tools
through the router without starting the full HTTP server.
"""

from llm.local_mcp.router import route_tool_call


def test_gmail_tool() -> None:
    """Test gmail.send tool (will fail without credentials)."""
    print("\n=== Testing gmail.send tool ===")
    
    arguments = {
        "to": "recipient@example.com",
        "subject": "Test Email from IncidentOps",
        "body": "This is a test email sent via the Local MCP Server."
    }
    
    try:
        result = route_tool_call('gmail.send', arguments)
        print(f"✓ Success: {result}")
    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_pushover_tool() -> None:
    """Test pushover.send tool (will fail without credentials)."""
    print("\n=== Testing pushover.send tool ===")
    
    arguments = {
        "user": "your_user_key_here",
        "message": "Test notification from IncidentOps",
        "title": "Test Alert",
        "priority": 1
    }
    
    try:
        result = route_tool_call('pushover.send', arguments)
        print(f"✓ Success: {result}")
    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_unknown_tool() -> None:
    """Test error handling for unknown tool."""
    print("\n=== Testing unknown tool ===")
    
    try:
        result = route_tool_call('unknown.tool', {})
        print(f"✗ Should have raised ValueError: {result}")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


if __name__ == '__main__':
    print("Local MCP Server Tools Test")
    print("=" * 50)
    print("\nNote: These tests will show configuration errors")
    print("unless you have set the required environment variables:")
    print("  - GMAIL_USER and GMAIL_PASSWORD for gmail.send")
    print("  - PUSHOVER_API_TOKEN for pushover.send")
    
    test_gmail_tool()
    test_pushover_tool()
    test_unknown_tool()
    
    print("\n" + "=" * 50)
    print("Test complete!")
