"""
Orchestrator module for IncidentOps pipeline execution.

This module ensures strict sequential data flow across all agents:
1. MonitorAgent → alerts (list of dicts with timestamp, level, message)
2. TriageAgent → triaged alerts (adds severity, category)
3. ResolutionAgent → resolution plans (adds recommended_actions)
4. OpsLogAgent → audit summary (dict with status, count, timestamp)

Each stage validates input/output data structures to prevent invalid data flow.
Pipeline execution stops immediately if any validation fails.
"""
from typing import Any, List, Dict
from agents.monitor_agent import MonitorAgent
from agents.triage_agent import TriageAgent
from agents.resolution_agent import ResolutionAgent
from agents.opslog_agent import OpsLogAgent


class PipelineExecutor:
    """
    Orchestrates strict sequential execution of the incident detection pipeline.
    Ensures data flow integrity and validates outputs between stages.
    """
    
    def __init__(self):
        """Initialize pipeline executor with agent instances."""
        self.agents = {
            'monitor': MonitorAgent("MonitorAgent"),
            'triage': TriageAgent("TriageAgent"),
            'resolution': ResolutionAgent("ResolutionAgent"),
            'opslog': OpsLogAgent("OpsLogAgent")
        }
        self.execution_log = []
    
    def _log_stage(self, stage_name: str, status: str, data_count: int = 0) -> None:
        """
        Log pipeline stage execution.
        
        Args:
            stage_name: Name of the pipeline stage
            status: Execution status (started, completed, failed)
            data_count: Number of data items processed
        """
        log_entry = {
            'stage': stage_name,
            'status': status,
            'data_count': data_count
        }
        self.execution_log.append(log_entry)
        
        if status == 'started':
            print(f"\n{'='*60}")
            print(f"Stage: {stage_name}")
            print(f"{'='*60}")
        elif status == 'completed':
            print(f"✓ {stage_name} completed with {data_count} item(s)")
        elif status == 'failed':
            print(f"✗ {stage_name} failed")
    
    def _validate_monitor_output(self, data: Any) -> List[Dict]:
        """
        Validate MonitorAgent output structure.
        
        Args:
            data: Output from MonitorAgent
            
        Returns:
            List[Dict]: Validated alert list
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, list):
            raise ValueError(f"MonitorAgent must return a list, got {type(data).__name__}")
        
        for idx, alert in enumerate(data):
            if not isinstance(alert, dict):
                raise ValueError(f"Alert {idx} must be a dict, got {type(alert).__name__}")
            
            required_fields = ['timestamp', 'level', 'message']
            missing_fields = [field for field in required_fields if field not in alert]
            if missing_fields:
                raise ValueError(f"Alert {idx} missing required fields: {missing_fields}")
        
        return data
    
    def _validate_triage_output(self, data: Any) -> List[Dict]:
        """
        Validate TriageAgent output structure.
        
        Args:
            data: Output from TriageAgent
            
        Returns:
            List[Dict]: Validated triaged alert list
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, list):
            raise ValueError(f"TriageAgent must return a list, got {type(data).__name__}")
        
        for idx, alert in enumerate(data):
            if not isinstance(alert, dict):
                raise ValueError(f"Triaged alert {idx} must be a dict, got {type(alert).__name__}")
            
            required_fields = ['timestamp', 'level', 'message', 'severity', 'category']
            missing_fields = [field for field in required_fields if field not in alert]
            if missing_fields:
                raise ValueError(f"Triaged alert {idx} missing required fields: {missing_fields}")
        
        return data
    
    def _validate_resolution_output(self, data: Any) -> List[Dict]:
        """
        Validate ResolutionAgent output structure.
        
        Args:
            data: Output from ResolutionAgent
            
        Returns:
            List[Dict]: Validated resolution plan list
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, list):
            raise ValueError(f"ResolutionAgent must return a list, got {type(data).__name__}")
        
        for idx, plan in enumerate(data):
            if not isinstance(plan, dict):
                raise ValueError(f"Resolution plan {idx} must be a dict, got {type(plan).__name__}")
            
            required_fields = ['alert_id', 'severity', 'category', 'recommended_actions']
            missing_fields = [field for field in required_fields if field not in plan]
            if missing_fields:
                raise ValueError(f"Resolution plan {idx} missing required fields: {missing_fields}")
            
            if not isinstance(plan.get('recommended_actions'), list):
                raise ValueError(f"Resolution plan {idx} 'recommended_actions' must be a list")
        
        return data
    
    def _validate_opslog_output(self, data: Any) -> Dict:
        """
        Validate OpsLogAgent output structure.
        
        Args:
            data: Output from OpsLogAgent
            
        Returns:
            Dict: Validated summary dictionary
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"OpsLogAgent must return a dict, got {type(data).__name__}")
        
        required_fields = ['status', 'count', 'timestamp']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"OpsLog summary missing required fields: {missing_fields}")
        
        return data
    
    def run(self) -> Dict:
        """
        Execute the complete pipeline with strict sequential data flow.
        
        Returns:
            Dict: Pipeline execution summary
            
        Raises:
            Exception: If any stage fails or data validation fails
        """
        try:
            # Stage 1: Monitor
            self._log_stage('MonitorAgent', 'started')
            alerts = self.agents['monitor'].run()
            alerts = self._validate_monitor_output(alerts)
            self._log_stage('MonitorAgent', 'completed', len(alerts))
            
            # Stage 2: Triage (depends on Monitor output)
            self._log_stage('TriageAgent', 'started')
            triaged = self.agents['triage'].run(alerts)
            triaged = self._validate_triage_output(triaged)
            self._log_stage('TriageAgent', 'completed', len(triaged))
            
            # Stage 3: Resolution (depends on Triage output)
            self._log_stage('ResolutionAgent', 'started')
            plans = self.agents['resolution'].run(triaged)
            plans = self._validate_resolution_output(plans)
            self._log_stage('ResolutionAgent', 'completed', len(plans))
            
            # Stage 4: OpsLog (depends on Resolution output)
            self._log_stage('OpsLogAgent', 'started')
            summary = self.agents['opslog'].run(plans)
            summary = self._validate_opslog_output(summary)
            self._log_stage('OpsLogAgent', 'completed', summary.get('count', 0))
            
            # Pipeline complete
            print(f"\n{'='*60}")
            print(f"✅ Pipeline completed successfully")
            print(f"{'='*60}")
            print(f"Summary: {summary}")
            
            return summary
            
        except ValueError as e:
            print(f"\n❌ Pipeline failed: Data validation error")
            print(f"   {str(e)}")
            raise
        except Exception as e:
            print(f"\n❌ Pipeline failed: {str(e)}")
            raise


def run_pipeline() -> Dict:
    """
    Execute the incident detection pipeline.
    
    Returns:
        Dict: Pipeline execution summary
    """
    executor = PipelineExecutor()
    return executor.run()
