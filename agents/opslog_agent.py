import json
import os
from datetime import datetime
from agents.base_agent import BaseAgent

class OpsLogAgent(BaseAgent):
    """
    OpsLogAgent generates factual, structured audit log entries for governance and traceability.
    
    This agent is responsible ONLY for:
    - Recording factual data from the pipeline execution
    - Persisting structured audit records to JSON
    - Maintaining execution timestamps and metadata
    
    This agent does NOT:
    - Perform interpretation or analysis
    - Generate human-readable summaries
    - Compute risk or make escalation decisions
    
    All interpretive logic belongs in LLMGovernanceAgent.
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
        Generate and persist factual audit log entry from resolution plans.
        
        Args:
            resolution_plans (list): List of resolution plan dictionaries from LLMResolutionAgent
            
        Returns:
            dict: Summary of logging operation with status and metadata
        """
        self.log("Recording factual audit log entry...")
        
        if not resolution_plans:
            self.log("No resolution plans to log.")
            return {"status": "no_data", "count": 0, "timestamp": None, "output_path": None}
        
        # Generate structured audit entry (factual data only)
        audit_entry = self._create_audit_entry(resolution_plans)
        
        # Persist to JSON file
        success = self._persist_audit_log(audit_entry)
        
        # Log operation status (factual only)
        if success:
            self.log(f"Audit log persisted: {len(resolution_plans)} incident(s) recorded")
        else:
            self.log("Failed to persist audit log")
        
        # Return operation summary
        return {
            "status": "logged" if success else "failed",
            "count": len(resolution_plans),
            "timestamp": audit_entry["execution_timestamp"],
            "output_path": self.output_path if success else None
        }
    
    def _create_audit_entry(self, resolution_plans):
        """
        Create factual structured audit log entry with pipeline execution data.
        
        This method records ONLY factual data without interpretation:
        - Timestamps
        - Counts and distributions
        - Raw resolution plans
        - Agent execution order
        
        Args:
            resolution_plans (list): List of resolution plan dictionaries
            
        Returns:
            dict: Structured audit entry with factual fields only
        """
        execution_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract factual stage outputs (counts and distributions only)
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
        
        # Agent execution order (factual record)
        agent_execution_order = [
            "MonitorAgent",
            "TriageAgent", 
            "LLMResolutionAgent",
            "OpsLogAgent"
        ]
        
        # Build complete audit entry (factual data only)
        audit_entry = {
            "execution_timestamp": execution_timestamp,
            "pipeline_name": "incident_detection",
            "agent_execution_order": agent_execution_order,
            "stage_outputs": stage_outputs,
            "resolution_plans": resolution_plans,
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
        
        This is a factual counting operation with no interpretation.
        
        Args:
            plans (list): List of plan dictionaries
            field (str): Field name to count
            
        Returns:
            dict: Dictionary with value counts
        """
        counts = {}
        for plan in plans:
            value = plan.get(field, 'unknown')
            # Convert priority numbers to labels for readability
            if field == 'priority':
                value = ['critical', 'high', 'medium', 'low'][value - 1] if isinstance(value, int) and 1 <= value <= 4 else str(value)
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts
    
    def _persist_audit_log(self, audit_entry):
        """
        Persist factual audit entry to JSON file.
        
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
