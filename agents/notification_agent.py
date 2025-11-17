"""
NotificationAgent sends alerts via email or push notifications using MCP tools.
This agent sits after LLMGovernanceAgent as the final stage in the pipeline.
"""
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from llm.mcp_client import MCPClient, MCPToolError, MCPConnectionError, MCPTimeoutError
from config.settings_loader import get_settings


class NotificationAgent(BaseAgent):
    """
    NotificationAgent sends notifications based on governance analysis results.
    Uses MCP tools for email and push notification delivery.
    
    Supported channels:
    - gmail: Sends email via gmail.send MCP tool
    - pushover: Sends push notification via pushover.send MCP tool
    """
    
    def __init__(self, name: str = "NotificationAgent", mcp_client: Optional[MCPClient] = None):
        """
        Initialize the Notification Agent.
        
        Args:
            name: Agent name for logging
            mcp_client: Optional MCPClient instance (for testing). If None, creates new instance.
        """
        super().__init__(name)
        
        # Load notification channels from settings
        settings = get_settings()
        self.notification_channels = settings.notification.channels or []
        
        # Initialize MCP client
        self.mcp_client = mcp_client if mcp_client is not None else MCPClient()
        
        self.log(f"Initialized with channels: {self.notification_channels}")
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notifications based on governance analysis.
        
        Args:
            input_data: Dictionary from LLMGovernanceAgent containing:
                - audit_summary: Original audit summary
                - governance_analysis: Governance report with risk, escalation, etc.
            
        Returns:
            Dict containing:
                - governance_output: Original governance output (passed through)
                - notification_status: Delivery status for each channel
                - notifications_sent: List of sent notifications with details
        """
        self.log("Processing notification requirements...")
        
        if not input_data or not isinstance(input_data, dict):
            self.log("No governance data to process.")
            return {
                'governance_output': input_data,
                'notification_status': 'skipped',
                'notifications_sent': []
            }
        
        governance_analysis = input_data.get('governance_analysis', {})
        audit_summary = input_data.get('audit_summary', {})
        
        # Determine if notification is required
        should_notify = self._should_send_notification(governance_analysis)
        
        if not should_notify:
            self.log("No notification required based on governance analysis.")
            return {
                'governance_output': input_data,
                'notification_status': 'not_required',
                'notifications_sent': []
            }
        
        # Prepare notification content
        notification_content = self._prepare_notification_content(
            governance_analysis, 
            audit_summary
        )
        
        # Send notifications via configured channels
        notifications_sent = []
        notification_status = 'success'
        
        for channel in self.notification_channels:
            try:
                result = self._send_notification(channel, notification_content)
                notifications_sent.append(result)
                self.log(f"✓ Notification sent via {channel}")
            except (MCPToolError, MCPConnectionError, MCPTimeoutError) as e:
                # Gracefully handle MCP errors without stopping the pipeline
                self.log(f"✗ MCP error sending notification via {channel}: {e}")
                notification_status = 'partial_failure'
                notifications_sent.append({
                    'channel': channel,
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                })
            except ValueError as e:
                # Handle configuration errors (missing secrets, unsupported channels)
                self.log(f"✗ Configuration error for {channel}: {e}")
                notification_status = 'partial_failure'
                notifications_sent.append({
                    'channel': channel,
                    'status': 'failed',
                    'error': str(e),
                    'error_type': 'ConfigurationError'
                })
            except Exception as e:
                # Catch any other unexpected errors
                self.log(f"✗ Unexpected error sending notification via {channel}: {e}")
                notification_status = 'partial_failure'
                notifications_sent.append({
                    'channel': channel,
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                })
        
        if not notifications_sent:
            notification_status = 'failed'
        elif all(n['status'] == 'failed' for n in notifications_sent):
            notification_status = 'failed'
        
        self.log(f"Notification delivery status: {notification_status}")
        
        return {
            'governance_output': input_data,
            'notification_status': notification_status,
            'notifications_sent': notifications_sent
        }
    
    def _should_send_notification(self, governance_analysis: Dict[str, Any]) -> bool:
        """
        Determine if notification should be sent based on governance analysis.
        
        Args:
            governance_analysis: Governance report with risk level and escalation
            
        Returns:
            bool: True if notification should be sent
        """
        risk_level = governance_analysis.get('risk', 'low').lower()
        escalation = governance_analysis.get('escalation', '').lower()
        
        # Send notification for high/critical risk or when escalation is required
        high_risk = risk_level in ['high', 'critical']
        escalation_required = escalation and 'none' not in escalation and 'no escalation' not in escalation
        
        return high_risk or escalation_required
    
    def _prepare_notification_content(
        self, 
        governance_analysis: Dict[str, Any],
        audit_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare notification content from governance analysis and audit summary.
        
        Args:
            governance_analysis: Governance report
            audit_summary: Audit summary from OpsLogAgent
            
        Returns:
            Dict: Notification content with subject, body, priority, etc.
        """
        risk_level = governance_analysis.get('risk', 'medium')
        escalation = governance_analysis.get('escalation', 'Review required')
        commentary = governance_analysis.get('commentary', '')
        compliance_issues = governance_analysis.get('compliance_issues', [])
        incident_count = audit_summary.get('count', 0)
        timestamp = audit_summary.get('timestamp', 'N/A')
        
        # Determine priority based on risk level
        priority_map = {
            'low': 'normal',
            'medium': 'normal',
            'high': 'high',
            'critical': 'urgent'
        }
        priority = priority_map.get(risk_level, 'normal')
        
        # Build subject line
        subject = f"[{risk_level.upper()}] IncidentOps Alert: {incident_count} incident(s) detected"
        
        # Build message body
        body_lines = [
            f"IncidentOps Governance Alert",
            f"",
            f"Risk Level: {risk_level.upper()}",
            f"Incidents Detected: {incident_count}",
            f"Timestamp: {timestamp}",
            f"",
            f"Escalation Required:",
            f"{escalation}",
            f"",
            f"Analysis:",
            f"{commentary}",
        ]
        
        if compliance_issues:
            body_lines.extend([
                f"",
                f"Compliance Issues:",
            ])
            for issue in compliance_issues:
                body_lines.append(f"  - {issue}")
        
        body_lines.extend([
            f"",
            f"Please review the full audit log for detailed information.",
            f"",
            f"---",
            f"This is an automated notification from IncidentOps."
        ])
        
        body = "\n".join(body_lines)
        
        return {
            'subject': subject,
            'body': body,
            'priority': priority,
            'risk_level': risk_level,
            'incident_count': incident_count,
            'timestamp': timestamp
        }
    
    def _send_notification(self, channel: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification via specified channel using MCP tools.
        
        Args:
            channel: Notification channel (gmail, pushover, etc.)
            content: Notification content dictionary
            
        Returns:
            Dict: Notification delivery result
            
        Raises:
            MCPToolError: If MCP tool invocation fails
        """
        # Map channel names to MCP tool names
        channel_tool_map = {
            'gmail': 'gmail.send',
            'pushover': 'pushover.send',
            # Future channels can be added here
            # 'slack': 'slack.send',
        }
        
        if channel not in channel_tool_map:
            raise ValueError(f"Unsupported notification channel: {channel}")
        
        tool_name = channel_tool_map[channel]
        
        # Prepare parameters based on channel type
        if channel == 'gmail':
            return self._send_gmail_notification(tool_name, content)
        elif channel == 'pushover':
            return self._send_pushover_notification(tool_name, content)
        else:
            raise ValueError(f"Unsupported notification channel: {channel}")
    
    def _send_gmail_notification(self, tool_name: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Gmail notification using MCP gmail.send tool.
        
        Args:
            tool_name: MCP tool name (gmail.send)
            content: Notification content dictionary
            
        Returns:
            Dict: Gmail delivery result
            
        Raises:
            MCPToolError: If MCP tool invocation fails
        """
        settings = get_settings()
        recipient = settings.get_secret('GMAIL_RECIPIENT')
        
        if not recipient:
            raise ValueError("GMAIL_RECIPIENT environment variable is required for gmail notifications")
        
        # Prepare parameters for gmail.send MCP tool
        params = {
            'to': recipient,
            'subject': content['subject'],
            'body': content['body']
        }
        
        self.log(f"Sending Gmail notification: {content['subject']}")
        
        # Call MCP tool
        result = self.mcp_client.call_tool(tool_name, params)
        
        if result['success']:
            self.log(f"Gmail notification sent successfully")
            return {
                'channel': 'gmail',
                'status': 'sent',
                'subject': content['subject'],
                'priority': content['priority'],
                'timestamp': content['timestamp'],
                'mcp_result': result['result'],
                'request_id': result['request_id']
            }
        else:
            error_msg = result['error']['message']
            self.log(f"Gmail notification failed: {error_msg}")
            raise MCPToolError(
                f"Gmail notification failed: {error_msg}",
                tool_name=tool_name,
                request_id=result['request_id'],
                server_error=result['error']
            )
    
    def _send_pushover_notification(self, tool_name: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Pushover notification using MCP pushover.send tool.
        
        Args:
            tool_name: MCP tool name (pushover.send)
            content: Notification content dictionary
            
        Returns:
            Dict: Pushover delivery result
            
        Raises:
            MCPToolError: If MCP tool invocation fails
        """
        settings = get_settings()
        user_key = settings.get_secret('PUSHOVER_USER_KEY')
        
        if not user_key:
            raise ValueError("PUSHOVER_USER_KEY environment variable is required for pushover notifications")
        
        # Map priority to Pushover priority levels
        # normal -> 0, high -> 1, urgent -> 2 (requires confirmation)
        priority_map = {
            'normal': 0,
            'high': 1,
            'urgent': 2
        }
        pushover_priority = priority_map.get(content['priority'], 0)
        
        # Prepare parameters for pushover.send MCP tool
        params = {
            'user': user_key,
            'message': content['body'],
            'title': content['subject'],
            'priority': pushover_priority
        }
        
        self.log(f"Sending Pushover notification: {content['subject']}")
        
        # Call MCP tool
        result = self.mcp_client.call_tool(tool_name, params)
        
        if result['success']:
            self.log(f"Pushover notification sent successfully")
            return {
                'channel': 'pushover',
                'status': 'sent',
                'subject': content['subject'],
                'priority': content['priority'],
                'timestamp': content['timestamp'],
                'mcp_result': result['result'],
                'request_id': result['request_id']
            }
        else:
            error_msg = result['error']['message']
            self.log(f"Pushover notification failed: {error_msg}")
            raise MCPToolError(
                f"Pushover notification failed: {error_msg}",
                tool_name=tool_name,
                request_id=result['request_id'],
                server_error=result['error']
            )
