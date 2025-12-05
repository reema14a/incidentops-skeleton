"""
Notifications Page

Displays notification settings, recent notification events, and allows configuration
of notification recipients. Provides test notification functionality.
"""

import streamlit as st
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Apply global theme
from ui.theme_loader import apply_global_theme, close_sidebar_wrapper
apply_global_theme()

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import database utilities
from db import db_util
from config.settings_loader import get_settings

# Import MCP client for test notifications
from llm.mcp_client import MCPClient, MCPToolError, MCPConnectionError, MCPTimeoutError


def get_enabled_channels() -> List[str]:
    """
    Get list of enabled notification channels from settings.
    
    Returns:
        List[str]: List of enabled channel names
    """
    try:
        settings = get_settings()
        channels = settings.notification.channels or []
        return channels
    except Exception as e:
        st.error(f"Error loading notification channels: {str(e)}")
        return []


def get_current_recipients(channel: str) -> List[str]:
    """
    Get current recipients for a channel from database.
    
    Args:
        channel: Channel name (e.g., 'gmail', 'pushover')
        
    Returns:
        List[str]: List of recipient email addresses or user keys
    """
    try:
        recipients = db_util.get_notification_settings(channel)
        return recipients
    except Exception as e:
        st.error(f"Error loading recipients for {channel}: {str(e)}")
        return []


def save_recipients(channel: str, recipients: List[str]) -> bool:
    """
    Save recipients for a channel to database.
    
    Args:
        channel: Channel name
        recipients: List of recipient addresses
        
    Returns:
        bool: True if save succeeded
    """
    try:
        success = db_util.update_notification_settings(channel, recipients)
        return success
    except Exception as e:
        st.error(f"Error saving recipients for {channel}: {str(e)}")
        return False


def get_recent_notifications(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent notification events from database.
    
    Args:
        limit: Maximum number of notifications to retrieve
        
    Returns:
        List[Dict]: List of notification event records
    """
    try:
        notifications = db_util.get_notifications()
        return notifications[:limit]
    except Exception as e:
        st.error(f"Error loading notification events: {str(e)}")
        return []


def send_test_notification(channel: str, recipients: List[str]) -> Dict[str, Any]:
    """
    Send a test notification via specified channel.
    
    Args:
        channel: Channel name (gmail, pushover)
        recipients: List of recipients
        
    Returns:
        Dict: Result of test notification
    """
    try:
        mcp_client = MCPClient()
        
        # Prepare test content
        test_content = {
            'subject': '[TEST] IncidentOps Notification Test',
            'body': 'This is a test notification from IncidentOps.\n\nIf you received this, your notification channel is configured correctly.',
            'priority': 'normal'
        }
        
        # Map channel to MCP tool
        channel_tool_map = {
            'gmail': 'gmail.send',
            'pushover': 'pushover.send'
        }
        
        if channel not in channel_tool_map:
            return {
                'success': False,
                'error': f'Unsupported channel: {channel}'
            }
        
        tool_name = channel_tool_map[channel]
        
        # Send test notification
        if channel == 'gmail':
            # Send to each recipient
            results = []
            for recipient in recipients:
                params = {
                    'to': recipient,
                    'subject': test_content['subject'],
                    'body': test_content['body']
                }
                result = mcp_client.call_tool(tool_name, params)
                results.append({
                    'recipient': recipient,
                    'success': result['success'],
                    'result': result.get('result'),
                    'error': result.get('error')
                })
            
            return {
                'success': all(r['success'] for r in results),
                'results': results
            }
            
        elif channel == 'pushover':
            # Pushover uses user key from environment
            settings = get_settings()
            user_key = settings.get_secret('PUSHOVER_USER_KEY')
            
            if not user_key:
                return {
                    'success': False,
                    'error': 'PUSHOVER_USER_KEY not configured'
                }
            
            params = {
                'user': user_key,
                'message': test_content['body'],
                'title': test_content['subject'],
                'priority': 0
            }


            
            result = mcp_client.call_tool(tool_name, params)
            
            return {
                'success': result['success'],
                'result': result.get('result'),
                'error': result.get('error')
            }
        
    except (MCPToolError, MCPConnectionError, MCPTimeoutError) as e:
        return {
            'success': False,
            'error': f'MCP error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def render_page():
    """Render the Notifications page."""
    
    # Page header
    st.title("🔔 Notifications")
    st.markdown("Configure notification channels and view recent notification events.")
    st.markdown("---")
    
    # Get enabled channels
    enabled_channels = get_enabled_channels()
    
    if not enabled_channels:
        st.warning("⚠️ No notification channels are currently enabled")
        st.info("""
        **To enable notification channels:**
        1. Set the `NOTIFICATION_CHANNELS` environment variable (e.g., `gmail,pushover`)
        2. Configure the required secrets for each channel
        3. Restart the application
        """)
        st.stop()
    
    # Display enabled channels
    st.subheader("📡 Enabled Channels")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Active Channels:**")
        for channel in enabled_channels:
            st.markdown(f"• {channel.capitalize()}")
    
    with col2:
        st.markdown("**Configuration Status:**")
        settings = get_settings()
        
        for channel in enabled_channels:
            if channel == 'gmail':
                # Check for Gmail secrets
                gmail_user = settings.get_secret('GMAIL_USER')
                gmail_pass = settings.get_secret('GMAIL_PASSWORD')
                
                if gmail_user and gmail_pass:
                    st.success(f"✓ Gmail configured")
                else:
                    st.error(f"✗ Gmail missing credentials — recipients stored but delivery will fail until configured")
                    
            elif channel == 'pushover':
                # Check for Pushover secrets
                pushover_token = settings.get_secret('PUSHOVER_API_TOKEN')
                pushover_user = settings.get_secret('PUSHOVER_USER_KEY')
                
                if pushover_token and pushover_user:
                    st.success(f"✓ Pushover configured")
                else:
                    st.error(f"✗ Pushover missing credentials")
    
    st.markdown("---")
    
    # Recipient Configuration Section
    st.subheader("📧 Recipient Configuration")
    
    # Create tabs for each channel
    if len(enabled_channels) == 1:
        # Single channel - no tabs needed
        channel = enabled_channels[0]
        render_channel_config(channel)
    else:
        # Multiple channels - use tabs
        tabs = st.tabs([f"{ch.capitalize()}" for ch in enabled_channels])
        
        for idx, channel in enumerate(enabled_channels):
            with tabs[idx]:
                render_channel_config(channel)
    
    st.markdown("---")
    
    # Recent Notification Events Section
    st.subheader("📜 Recent Notification Events")
    
    recent_notifications = get_recent_notifications(limit=20)
    
    if not recent_notifications:
        st.info("No notification events found in database")
        st.markdown("""
        **Notification events will appear here after:**
        1. Running the pipeline with high/critical risk incidents
        2. Triggering escalation conditions
        3. Sending test notifications
        """)
    else:
        st.markdown(f"Showing {len(recent_notifications)} most recent notification(s)")
        
        # Display notifications in a table
        import pandas as pd
        
        table_data = []
        for notif in recent_notifications:
            # Parse response if it's JSON
            response_text = notif.get('response', '')
            try:
                response_json = json.loads(response_text)
                response_display = json.dumps(response_json, indent=2)
            except:
                response_display = response_text
            
            # Truncate long responses
            if len(response_display) > 100:
                response_display = response_display[:97] + "..."
            
            table_data.append({
                'Run ID': f"#{notif.get('run_id')}",
                'Channel': notif.get('channel', 'N/A').capitalize(),
                'Status': notif.get('status', 'N/A'),
                'Response': response_display
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Detailed view in expanders
        st.markdown("---")
        st.markdown("**Detailed Event View:**")
        
        for idx, notif in enumerate(recent_notifications[:10]):  # Show details for first 10
            with st.expander(f"Run #{notif.get('run_id')} - {notif.get('channel', 'N/A').capitalize()} - {notif.get('status', 'N/A')}"):
                st.markdown(f"**Notification ID:** {notif.get('id')}")
                st.markdown(f"**Pipeline Run ID:** {notif.get('run_id')}")
                st.markdown(f"**Channel:** {notif.get('channel', 'N/A')}")
                st.markdown(f"**Status:** {notif.get('status', 'N/A')}")
                st.markdown(f"**Response:**")
                
                # Try to display response as JSON
                response_text = notif.get('response', '')
                try:
                    response_json = json.loads(response_text)
                    st.json(response_json)
                except:
                    st.code(response_text)


def render_channel_config(channel: str):
    """
    Render configuration UI for a specific channel.
    
    Args:
        channel: Channel name (gmail, pushover)
    """

    # Always define current_recipients so nothing breaks inside the Test button
    current_recipients = get_current_recipients(channel) if channel != "pushover" else []

    if channel != 'pushover':
        st.markdown(f"**Current Recipients for {channel.capitalize()}:**")
        
        if current_recipients:
            for recipient in current_recipients:
                st.markdown(f"• {recipient}")
        else:
            st.info(f"No recipients configured for {channel}")

        st.markdown("---")

    
    # Editable recipient input
    if channel == 'gmail':
        st.markdown("**Configure Email Recipients:**")
        st.caption("Enter one or more email addresses (comma-separated)")
        
        # Text area for multiple emails
        recipients_input = st.text_area(
            "Email Addresses",
            value=", ".join(current_recipients) if current_recipients else "",
            placeholder="user1@example.com, user2@example.com",
            key=f"{channel}_recipients_input",
            label_visibility="collapsed"
        )
        
    elif channel == 'pushover':
        st.markdown("**Configure Pushover Recipients:**")
        st.caption("Pushover uses the PUSHOVER_USER_KEY environment variable")
        st.info("Pushover notifications are sent to the user key configured in your environment variables. No additional recipient configuration is needed.")
        recipients_input = None

    else:
        st.warning(f"Configuration UI not implemented for {channel}")
        recipients_input = None
    
    # Save button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if recipients_input is not None and channel == 'gmail':
            if st.button(f"💾 Save Recipients", key=f"{channel}_save_btn", use_container_width=True):
                # Parse recipients
                new_recipients = [r.strip() for r in recipients_input.split(',') if r.strip()]
                
                if not new_recipients:
                    st.error("Please enter at least one recipient")
                else:
                    # Save to database
                    success = save_recipients(channel, new_recipients)
                    
                    if success:
                        st.success(f"✓ Recipients saved for {channel}")
                        st.session_state["reload_notifications"] = True
                    else:
                        st.error(f"✗ Failed to save recipients for {channel}")
        elif channel == 'pushover':
            st.markdown("**Test Pushover Notification:**")
        #     st.caption("Pushover notifications are sent to the user key configured in your environment variables")
    
    with col2:
        # Test notification button
        if st.button(f"📤 Send Test Notification", key=f"{channel}_test_btn", use_container_width=True):
            with st.spinner(f"Sending test notification via {channel}... to {current_recipients}"):
                # Get recipients to test
                test_recipients = current_recipients
                
                if channel == 'gmail' and not test_recipients:
                    st.error("Please configure and save recipients before sending test notification")
                else:
                    result = send_test_notification(channel, test_recipients)
                    
                    if result.get('success'):
                        st.success(f"✓ Test notification sent successfully via {channel}")
                        
                        # Show detailed results for gmail (multiple recipients)
                        if channel == 'gmail' and 'results' in result:
                            with st.expander("View Delivery Details"):
                                for r in result['results']:
                                    if r['success']:
                                        st.success(f"✓ Sent to {r['recipient']}")
                                    else:
                                        st.error(f"✗ Failed to send to {r['recipient']}: {r.get('error', {}).get('message', 'Unknown error')}")
                    else:
                        st.error(f"✗ Test notification failed: {result.get('error', 'Unknown error')}")


# Render the page when loaded by Streamlit
# (Streamlit sets __name__ to the module path, not "__main__")
try:
    # Only render if we're in a Streamlit context (not during testing)
    import streamlit as st
    if hasattr(st, 'runtime') and st.runtime.exists():
        render_page()
except:
    # During testing or import, don't render
    pass

# Close sidebar wrapper
close_sidebar_wrapper()
