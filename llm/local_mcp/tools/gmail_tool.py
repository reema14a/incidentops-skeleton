"""Gmail tool implementation for Local MCP Server.

Sends emails using SMTP with Gmail credentials from environment variables.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict
from config.settings_loader import get_settings

logger = logging.getLogger("LocalMCPServer")


def gmail_send(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Send an email via Gmail SMTP.
    
    Args:
        arguments: Tool arguments containing:
            - to (str): Recipient email address
            - subject (str): Email subject
            - body (str): Email body content
            
    Returns:
        dict: Result with success status and message.
        
    Raises:
        ValueError: If required arguments are missing.
        Exception: If email sending fails.
    """
    # Validate required arguments
    required_fields = ['to', 'subject', 'body']
    for field in required_fields:
        if field not in arguments:
            logger.error(f"Missing required field: {field}")
            raise ValueError(f"Missing required argument: {field}")
    
    to_email = arguments['to']
    subject = arguments['subject']
    body = arguments['body']
    
    logger.info(f"Sending email to {to_email} with subject: {subject}")
    
    # Get Gmail credentials from environment
    settings = get_settings()
    gmail_user = settings.get_secret('GMAIL_USER')
    gmail_password = settings.get_secret('GMAIL_PASSWORD')
    
    if not gmail_user or not gmail_password:
        logger.error("Gmail credentials not configured")
        raise ValueError(
            "Gmail credentials not configured. "
            "Set GMAIL_USER and GMAIL_PASSWORD environment variables."
        )
    
    try:
        # Create message
        message = MIMEMultipart()
        message['From'] = gmail_user
        message['To'] = to_email
        message['Subject'] = subject
        
        # Attach body
        message.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP server
        logger.debug("Connecting to Gmail SMTP server")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            
            # Send email
            text = message.as_string()
            server.sendmail(gmail_user, to_email, text)
        
        logger.info(f"Email sent successfully to {to_email}")
        
        return {
            "success": True,
            "message": f"Email sent to {to_email}",
            "recipient": to_email,
            "subject": subject
        }
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Gmail authentication failed: {e}")
        raise Exception(f"Gmail authentication failed. Check credentials: {e}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        raise Exception(f"Failed to send email via SMTP: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        raise Exception(f"Failed to send email: {e}")
