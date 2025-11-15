import json
import os
from datetime import datetime
from agents.base_agent import BaseAgent

class OpsLogAgent(BaseAgent):
    """
    OpsLogAgent generates structured audit log entries for governance and traceability.
    Persists incident resolution data to JSON format with full pipeline context.
    """
    
    def __init__(self, name, output_path="data/output_log.json"):
        """
        Initialize OpsLogAgent with output path.
        
        Args:
            name (str): Agent name for logging
            output_path (str): Path to output JSON log file
        """
        super().__init__(name)
        self.output_path = output_path
    
    def run(self, resolution_plans):
        """
        Generate and persist audit log entry from resolution plans.
        
        Args:
            resolution_plans (list): List of resolution plan dictionaries from ResolutionAgent
            
        Returns:
            dict: Summary of logging operation with status and metadata
        """
        self.log("Generating audit log entry...")
        
        if not resolution_plans:
            self.log("No resolution plans to log.")
            return {"status": "no_data", "count": 0, "timestamp": None, "output_path": None}
        
        # Generate structured audit entry
        audit_entry = self._create_audit_entry(resolution_plans)
        
        # Persist to JSON file
        success = self._persist_audit_log(audit_entry)
        
        # Log summary
        self._log_summary(audit_entry, success)
        
        # Return operation summary
        return {
            "status": "logged" if success else "failed",
            "count": len(resolution_plans),
            "timestamp": audit_entry["execution_timestamp"],
            "output_path": self.output_path if success else None
        }
    
    def _create_audit_entry(self, resolution_plans):
        """
        Create structured audit log entry with full pipeline context.
        
        Args:
            resolution_plans (list): List of resolution plan dictionaries
            
        Returns:
            dict: Structured audit entry with all required fields
        """
        execution_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract stage outputs
        stage_outputs = {
            "monitor_stage": {
                "alerts_detected": len(resolution_plans),
                "alert_ids": [plan['alert_id'] for plan in resolution_plans]
            },
            "triage_stage": {
                "severity_distribution": self._count_by_field(resolution_plans, 'severity'),
                "category_distribution": self._count_by_field(resolution_plans, 'category')
            },
            "resolution_stage": {
                "plans_generated": len(resolution_plans),
                "priority_distribution": self._count_by_field(resolution_plans, 'priority')
            }
        }
        
        # Agent execution order
        agent_execution_order = [
            "MonitorAgent",
            "TriageAgent", 
            "ResolutionAgent",
            "OpsLogAgent"
        ]
        
        # Generate summary of recommendations
        recommendations_summary = self._generate_recommendations_summary(resolution_plans)
        
        # Build complete audit entry
        audit_entry = {
            "execution_timestamp": execution_timestamp,
            "pipeline_name": "incident_detection",
            "agent_execution_order": agent_execution_order,
            "stage_outputs": stage_outputs,
            "resolution_plans": resolution_plans,
            "recommendations_summary": recommendations_summary,
            "total_incidents": len(resolution_plans),
            "audit_metadata": {
                "logged_by": self.name,
                "log_version": "1.0",
                "entry_id": f"audit_{execution_timestamp.replace(' ', '_').replace(':', '-')}"
            }
        }
        
        return audit_entry
    
    def _count_by_field(self, plans, field):
        """
        Count occurrences of values for a specific field in plans.
        
        Args:
            plans (list): List of plan dictionaries
            field (str): Field name to count
            
        Returns:
            dict: Dictionary with value counts
        """
        counts = {}
        for plan in plans:
            value = plan.get(field, 'unknown')
            # Convert priority numbers to labels
            if field == 'priority':
                value = ['critical', 'high', 'medium', 'low'][value - 1] if isinstance(value, int) and 1 <= value <= 4 else str(value)
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts
    
    def _generate_recommendations_summary(self, resolution_plans):
        """
        Generate high-level summary of all recommendations.
        
        Args:
            resolution_plans (list): List of resolution plan dictionaries
            
        Returns:
            dict: Summary of recommendations by priority and category
        """
        summary = {
            "total_actions": sum(len(plan.get('recommended_actions', [])) for plan in resolution_plans),
            "high_priority_count": sum(1 for plan in resolution_plans if plan.get('priority', 4) <= 2),
            "categories_affected": list(set(plan.get('category', 'unknown') for plan in resolution_plans)),
            "critical_actions": []
        }
        
        # Extract critical actions (priority 1)
        for plan in resolution_plans:
            if plan.get('priority') == 1:
                summary["critical_actions"].append({
                    "alert_id": plan.get('alert_id'),
                    "category": plan.get('category'),
                    "actions": plan.get('recommended_actions', [])
                })
        
        return summary
    
    def _persist_audit_log(self, audit_entry):
        """
        Persist audit entry to JSON file.
        
        Args:
            audit_entry (dict): Structured audit entry
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Load existing logs if file exists
            existing_logs = []
            if os.path.exists(self.output_path):
                try:
                    with open(self.output_path, 'r') as f:
                        existing_logs = json.load(f)
                        if not isinstance(existing_logs, list):
                            existing_logs = [existing_logs]
                except json.JSONDecodeError:
                    self.log("Warning: Existing log file is invalid, will overwrite")
                    existing_logs = []
            
            # Append new entry
            existing_logs.append(audit_entry)
            
            # Write to file with pretty formatting
            with open(self.output_path, 'w') as f:
                json.dump(existing_logs, f, indent=2)
            
            self.log(f"Audit log written to {self.output_path}")
            return True
            
        except Exception as e:
            self.log(f"Error writing audit log: {str(e)}")
            return False
    
    def _log_summary(self, audit_entry, success):
        """
        Log summary of audit entry creation.
        
        Args:
            audit_entry (dict): The created audit entry
            success (bool): Whether persistence was successful
        """
        if success:
            self.log(f"Logged {audit_entry['total_incidents']} incident(s)")
            
            # Log severity breakdown
            severity_dist = audit_entry['stage_outputs']['triage_stage']['severity_distribution']
            self.log(f"  Severity: {', '.join(f'{k}({v})' for k, v in severity_dist.items())}")
            
            # Log category breakdown
            category_dist = audit_entry['stage_outputs']['triage_stage']['category_distribution']
            self.log(f"  Categories: {', '.join(f'{k}({v})' for k, v in category_dist.items())}")
            
            # Log high priority count
            high_priority = audit_entry['recommendations_summary']['high_priority_count']
            if high_priority > 0:
                self.log(f"  ⚠️  {high_priority} high-priority incident(s) require immediate attention")
        else:
            self.log("Failed to persist audit log")
