from agents.base_agent import BaseAgent

class TriageAgent(BaseAgent):
    """
    TriageAgent classifies alerts by severity and category.
    Takes alert events from MonitorAgent and enriches them with classification metadata.
    """
    
    def __init__(self, name):
        super().__init__(name)
        
        # Define severity classification rules based on keywords
        self.severity_rules = {
            'critical': ['crash', 'fatal', 'down', 'outage', 'unavailable'],
            'high': ['timeout', 'failed', 'failure', 'error', 'exception'],
            'medium': ['warning', 'degraded', 'slow', 'threshold'],
            'low': ['info', 'notice', 'debug']
        }
        
        # Define category classification rules based on keywords
        self.category_rules = {
            'database': ['database', 'db', 'sql', 'query', 'connection pool'],
            'network': ['network', 'timeout', 'connection', 'socket', 'dns'],
            'memory': ['memory', 'heap', 'oom', 'allocation', 'leak'],
            'disk': ['disk', 'storage', 'filesystem', 'io', 'space'],
            'performance': ['slow', 'latency', 'performance', 'threshold', 'degraded'],
            'security': ['security', 'auth', 'unauthorized', 'forbidden', 'breach'],
            'application': ['application', 'service', 'process', 'runtime']
        }
    
    def run(self, alerts):
        """
        Classifies alerts by severity and category.
        
        Args:
            alerts: List of alert dictionaries from MonitorAgent
            
        Returns:
            list: List of triaged alert dictionaries with severity and category
        """
        self.log("Classifying alerts...")
        
        if not alerts:
            self.log("No alerts to triage.")
            return []
        
        triaged_alerts = []
        
        for alert in alerts:
            triaged_alert = self._classify_alert(alert)
            triaged_alerts.append(triaged_alert)
        
        # Log summary statistics
        self._log_triage_summary(triaged_alerts)
        
        self.log("Triage complete.")
        return triaged_alerts
    
    def _classify_alert(self, alert):
        """
        Classify a single alert by severity and category.
        
        Args:
            alert: Alert dictionary with timestamp, level, message, etc.
            
        Returns:
            dict: Enriched alert with severity and category fields
        """
        message = alert.get('message', '').lower()
        level = alert.get('level', 'INFO')
        
        # Determine severity
        severity = self._determine_severity(message, level)
        
        # Determine category
        category = self._determine_category(message)
        
        # Create triaged alert with original data plus classification
        triaged_alert = {
            **alert,  # Include all original alert fields
            'severity': severity,
            'category': category
        }
        
        return triaged_alert
    
    def _determine_severity(self, message, level):
        """
        Determine severity based on message content and log level.
        
        Args:
            message: Alert message (lowercase)
            level: Original log level (ERROR, WARNING, etc.)
            
        Returns:
            str: Severity level (critical, high, medium, low)
        """
        # Check severity rules in order of priority
        for severity, keywords in self.severity_rules.items():
            for keyword in keywords:
                if keyword in message:
                    return severity
        
        # Fallback based on log level
        if level == 'ERROR':
            return 'high'
        elif level == 'WARNING':
            return 'medium'
        else:
            return 'low'
    
    def _determine_category(self, message):
        """
        Determine category based on message content.
        
        Args:
            message: Alert message (lowercase)
            
        Returns:
            str: Category name or 'general' if no match
        """
        # Check category rules
        for category, keywords in self.category_rules.items():
            for keyword in keywords:
                if keyword in message:
                    return category
        
        # Default category
        return 'general'
    
    def _log_triage_summary(self, triaged_alerts):
        """
        Log summary statistics of triaged alerts.
        
        Args:
            triaged_alerts: List of triaged alert dictionaries
        """
        total = len(triaged_alerts)
        self.log(f"Triaged {total} alert(s):")
        
        # Count by severity
        severity_counts = {}
        for alert in triaged_alerts:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                self.log(f"  - {severity.upper()}: {count}")
        
        # Count by category
        category_counts = {}
        for alert in triaged_alerts:
            category = alert['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        if category_counts:
            self.log(f"Categories: {', '.join(f'{cat}({cnt})' for cat, cnt in sorted(category_counts.items()))}")
