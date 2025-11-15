from agents.base_agent import BaseAgent

class ResolutionAgent(BaseAgent):
    """
    ResolutionAgent proposes remediation actions based on triaged alerts.
    Uses severity and category to map to appropriate resolution steps.
    """
    
    def __init__(self, name):
        super().__init__(name)
        
        # Define resolution mapping based on category and severity
        self.resolution_map = {
            'database': {
                'critical': [
                    'Initiate database failover to standby instance',
                    'Alert DBA team immediately',
                    'Check database connection pool status'
                ],
                'high': [
                    'Restart database connection pool',
                    'Check for long-running queries',
                    'Review database logs for errors'
                ],
                'medium': [
                    'Monitor database performance metrics',
                    'Review slow query log',
                    'Check database disk space'
                ],
                'low': [
                    'Log database event for review',
                    'Schedule routine database maintenance check'
                ]
            },
            'network': {
                'critical': [
                    'Escalate to network operations team',
                    'Check network infrastructure status',
                    'Verify DNS and routing configuration'
                ],
                'high': [
                    'Restart affected network services',
                    'Check firewall rules and connectivity',
                    'Review network latency metrics'
                ],
                'medium': [
                    'Monitor network performance',
                    'Check for packet loss or high latency',
                    'Review network logs'
                ],
                'low': [
                    'Log network event for analysis',
                    'Schedule network health check'
                ]
            },
            'memory': {
                'critical': [
                    'Restart affected service immediately',
                    'Increase memory allocation if possible',
                    'Investigate memory leak'
                ],
                'high': [
                    'Analyze heap dump',
                    'Review memory usage trends',
                    'Consider scaling up resources'
                ],
                'medium': [
                    'Monitor memory usage patterns',
                    'Review application memory configuration',
                    'Check for memory-intensive operations'
                ],
                'low': [
                    'Log memory event',
                    'Schedule memory profiling session'
                ]
            },
            'disk': {
                'critical': [
                    'Free up disk space immediately',
                    'Archive or delete old logs',
                    'Expand storage capacity'
                ],
                'high': [
                    'Clean up temporary files',
                    'Review disk usage by directory',
                    'Implement log rotation'
                ],
                'medium': [
                    'Monitor disk usage trends',
                    'Review storage allocation',
                    'Plan capacity expansion'
                ],
                'low': [
                    'Log disk usage event',
                    'Schedule storage review'
                ]
            },
            'performance': {
                'critical': [
                    'Scale up resources immediately',
                    'Enable performance degradation mode',
                    'Alert performance team'
                ],
                'high': [
                    'Analyze performance bottlenecks',
                    'Review resource utilization',
                    'Consider horizontal scaling'
                ],
                'medium': [
                    'Monitor performance metrics',
                    'Review application profiling data',
                    'Optimize slow operations'
                ],
                'low': [
                    'Log performance event',
                    'Schedule performance review'
                ]
            },
            'security': {
                'critical': [
                    'Isolate affected systems immediately',
                    'Alert security team',
                    'Initiate incident response protocol'
                ],
                'high': [
                    'Review authentication logs',
                    'Check for unauthorized access attempts',
                    'Verify security policies'
                ],
                'medium': [
                    'Monitor security events',
                    'Review access control lists',
                    'Update security configurations'
                ],
                'low': [
                    'Log security event',
                    'Schedule security audit'
                ]
            },
            'application': {
                'critical': [
                    'Restart application service',
                    'Rollback recent deployment if applicable',
                    'Alert development team'
                ],
                'high': [
                    'Review application logs',
                    'Check service health endpoints',
                    'Analyze error stack traces'
                ],
                'medium': [
                    'Monitor application metrics',
                    'Review recent code changes',
                    'Check configuration settings'
                ],
                'low': [
                    'Log application event',
                    'Schedule code review'
                ]
            },
            'general': {
                'critical': [
                    'Escalate to on-call engineer',
                    'Review system status',
                    'Initiate emergency response'
                ],
                'high': [
                    'Investigate error details',
                    'Review system logs',
                    'Check service dependencies'
                ],
                'medium': [
                    'Monitor system health',
                    'Review error patterns',
                    'Document issue for analysis'
                ],
                'low': [
                    'Log event for review',
                    'Schedule routine investigation'
                ]
            }
        }
    
    def run(self, triaged_alerts):
        """
        Generate remediation plans for triaged alerts.
        
        Args:
            triaged_alerts: List of triaged alert dictionaries with severity and category
            
        Returns:
            list: List of resolution plan dictionaries
        """
        self.log("Generating remediation plans...")
        
        if not triaged_alerts:
            self.log("No alerts to resolve.")
            return []
        
        resolution_plans = []
        
        for alert in triaged_alerts:
            plan = self._create_resolution_plan(alert)
            resolution_plans.append(plan)
        
        # Log summary
        self._log_resolution_summary(resolution_plans)
        
        self.log("Resolution plans created.")
        return resolution_plans
    
    def _create_resolution_plan(self, alert):
        """
        Create a resolution plan for a single alert.
        
        Args:
            alert: Triaged alert dictionary with severity, category, and alert details
            
        Returns:
            dict: Resolution plan with alert info and recommended actions
        """
        severity = alert.get('severity', 'low')
        category = alert.get('category', 'general')
        
        # Get recommended actions from resolution map
        actions = self._get_recommended_actions(category, severity)
        
        # Create resolution plan
        plan = {
            'alert_id': f"{alert.get('timestamp', 'unknown')}_{alert.get('line_number', 0)}",
            'timestamp': alert.get('timestamp'),
            'severity': severity,
            'category': category,
            'message': alert.get('message', ''),
            'recommended_actions': actions,
            'priority': self._calculate_priority(severity),
            'reasoning': self._generate_reasoning(category, severity)
        }
        
        return plan
    
    def _get_recommended_actions(self, category, severity):
        """
        Get recommended actions from resolution map.
        
        Args:
            category: Alert category
            severity: Alert severity level
            
        Returns:
            list: List of recommended action strings
        """
        # Get category-specific actions, fallback to general
        category_actions = self.resolution_map.get(category, self.resolution_map['general'])
        
        # Get severity-specific actions
        actions = category_actions.get(severity, category_actions.get('medium', []))
        
        return actions
    
    def _calculate_priority(self, severity):
        """
        Calculate numeric priority based on severity.
        
        Args:
            severity: Severity level string
            
        Returns:
            int: Priority number (1=highest, 4=lowest)
        """
        priority_map = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        return priority_map.get(severity, 3)
    
    def _generate_reasoning(self, category, severity):
        """
        Generate reasoning explanation for the resolution plan.
        
        Args:
            category: Alert category
            severity: Alert severity level
            
        Returns:
            str: Reasoning explanation
        """
        return f"Based on {severity} severity {category} incident, recommended actions prioritize immediate stabilization and root cause analysis."
    
    def _log_resolution_summary(self, resolution_plans):
        """
        Log summary of resolution plans.
        
        Args:
            resolution_plans: List of resolution plan dictionaries
        """
        total = len(resolution_plans)
        self.log(f"Created {total} resolution plan(s):")
        
        # Count by priority
        priority_counts = {}
        for plan in resolution_plans:
            priority = plan['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority in sorted(priority_counts.keys()):
            count = priority_counts[priority]
            priority_label = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'][priority - 1]
            self.log(f"  - Priority {priority} ({priority_label}): {count} plan(s)")
