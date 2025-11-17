"""Pushover tool implementation for Local MCP Server.

Sends push notifications using Pushover REST API.
"""

import logging
import requests
from typing import Any, Dict, Optional
from config.settings_loader import get_settings

logger = logging.getLogger("LocalMCPServer")

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


def pushover_send(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Send a push notification via Pushover API.
    
    Args:
        arguments: Tool arguments containing:
            - user (str): Pushover user key
            - message (str): Notification message
            - title (str, optional): Notification title
            - priority (int, optional): Priority level (-2 to 2)
            
    Returns:
        dict: Result with success status and message.
        
    Raises:
        ValueError: If required arguments are missing.
        Exception: If notification sending fails.
    """
    # Validate required arguments
    required_fields = ['user', 'message']
    for field in required_fields:
        if field not in arguments:
            logger.error(f"Missing required field: {field}")
            raise ValueError(f"Missing required argument: {field}")
    
    user_key = arguments['user']
    message = arguments['message']
    title = arguments.get('title', 'IncidentOps Notification')
    priority = arguments.get('priority', 0)
    
    logger.info(f"Sending Pushover notification to user {user_key[:8]}...")
    
    # Get Pushover API token from environment
    settings = get_settings()
    pushover_token = settings.get_secret('PUSHOVER_API_TOKEN')
    
    if not pushover_token:
        logger.error("Pushover API token not configured")
        raise ValueError(
            "Pushover API token not configured. "
            "Set PUSHOVER_API_TOKEN environment variable."
        )
    
    try:
        # Prepare API request
        payload = {
            'token': pushover_token,
            'user': user_key,
            'message': message,
            'title': title,
            'priority': priority
        }
        
        logger.debug(f"Sending request to Pushover API")
        
        # Send POST request to Pushover API
        response = requests.post(
            PUSHOVER_API_URL,
            data=payload,
            timeout=10
        )
        
        # Check response status
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('status') == 1:
                logger.info(f"Pushover notification sent successfully")
                return {
                    "success": True,
                    "message": "Notification sent successfully",
                    "request_id": response_data.get('request')
                }
            else:
                errors = response_data.get('errors', [])
                logger.error(f"Pushover API returned error: {errors}")
                raise Exception(f"Pushover API error: {errors}")
        else:
            logger.error(f"Pushover API returned status {response.status_code}: {response.text}")
            raise Exception(
                f"Pushover API request failed with status {response.status_code}: {response.text}"
            )
    
    except requests.exceptions.Timeout as e:
        logger.error(f"Pushover API request timed out: {e}")
        raise Exception(f"Pushover API request timed out: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Pushover API request failed: {e}")
        raise Exception(f"Failed to send Pushover notification: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending Pushover notification: {e}")
        raise Exception(f"Failed to send Pushover notification: {e}")
