import os
import re
from datetime import datetime
from agents.base_agent import BaseAgent

class MonitorAgent(BaseAgent):
    """
    MonitorAgent scans logs and metrics for anomalies and generates alert events.
    Reads from log files and detects ERROR and WARNING level messages.
    """
    
    def __init__(self, name, log_path="data/sample_logs.txt"):
        super().__init__(name)
        self.log_path = log_path
        self.alert_patterns = {
            'ERROR': r'ERROR\s+(.+)',
            'WARNING': r'WARNING\s+(.+)'
        }
    
    def run(self, _=None):
        """
        Scans log files for anomalies and returns a list of alert events.
        
        Returns:
            list: List of alert dictionaries with timestamp, level, and message
        """
        self.log("Scanning logs for anomalies...")
        alerts = []
        
        if not os.path.exists(self.log_path):
            self.log(f"Warning: Log file not found at {self.log_path}")
            return alerts
        
        try:
            with open(self.log_path, 'r') as log_file:
                for line_num, line in enumerate(log_file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse log line for timestamp and level
                    alert = self._parse_log_line(line, line_num)
                    if alert:
                        alerts.append(alert)
            
            self.log(f"Detected {len(alerts)} alerts.")
            
            # Log summary by severity
            if alerts:
                error_count = sum(1 for a in alerts if a['level'] == 'ERROR')
                warning_count = sum(1 for a in alerts if a['level'] == 'WARNING')
                self.log(f"  - {error_count} ERROR(s)")
                self.log(f"  - {warning_count} WARNING(s)")
            
            return alerts
            
        except Exception as e:
            self.log(f"Error reading log file: {str(e)}")
            return alerts
    
    def _parse_log_line(self, line, line_num):
        """
        Parse a single log line and extract alert information.
        
        Args:
            line: Log line string
            line_num: Line number in the file
            
        Returns:
            dict: Alert dictionary or None if no alert detected
        """
        # Try to match ERROR or WARNING patterns
        for level, pattern in self.alert_patterns.items():
            match = re.search(pattern, line)
            if match:
                message = match.group(1).strip()
                
                # Try to extract timestamp from beginning of line
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                return {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message,
                    'line_number': line_num,
                    'raw_log': line
                }
        
        return None
