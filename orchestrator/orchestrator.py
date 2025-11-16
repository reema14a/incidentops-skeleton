"""
Orchestrator module for IncidentOps pipeline execution.

This module ensures strict sequential data flow across all agents:
1. MonitorAgent → alerts (list of dicts with timestamp, level, message)
2. LLMAlertSummaryAgent → enriched alerts with LLM summary
3. TriageAgent → triaged alerts (adds severity, category)
4. LLMResolutionAgent → resolution plans with LLM-generated recommendations and summary
5. OpsLogAgent → audit summary (dict with status, count, timestamp)
6. LLMGovernanceAgent → governance analysis (risk scoring, escalation, compliance)

Each stage validates input/output data structures to prevent invalid data flow.
Pipeline execution stops immediately if any validation fails.
"""
from typing import Any, List, Dict
from agents.monitor_agent import MonitorAgent
from agents.llm_alert_summary_agent import LLMAlertSummaryAgent
from agents.triage_agent import TriageAgent
from agents.llm_resolution_agent import LLMResolutionAgent
from agents.opslog_agent import OpsLogAgent
from agents.llm_governance_agent import LLMGovernanceAgent


class PipelineExecutor:
    """
    Orchestrates strict sequential execution of the incident detection pipeline.
    Ensures data flow integrity and validates outputs between stages.
    """
    
    def __init__(self):
        """Initialize pipeline executor with agent instances."""
        self.agents = {
            'monitor': MonitorAgent("MonitorAgent"),
            'llm_summary': LLMAlertSummaryAgent("LLMAlertSummaryAgent"),
            'triage': TriageAgent("TriageAgent"),
            'llm_resolution': LLMResolutionAgent("LLMResolutionAgent"),
            'opslog': OpsLogAgent("OpsLogAgent"),
            'governance': LLMGovernanceAgent("LLMGovernanceAgent")
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
    
    def _validate_llm_summary_output(self, data: Any) -> Dict:
        """
        Validate LLMAlertSummaryAgent output structure.
        
        Args:
            data: Output from LLMAlertSummaryAgent
            
        Returns:
            Dict: Validated output with alerts and llm_summary
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"LLMAlertSummaryAgent must return a dict, got {type(data).__name__}")
        
        required_fields = ['alerts', 'llm_summary']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"LLMAlertSummaryAgent output missing required fields: {missing_fields}")
        
        if not isinstance(data['alerts'], list):
            raise ValueError(f"LLMAlertSummaryAgent 'alerts' must be a list, got {type(data['alerts']).__name__}")
        
        if not isinstance(data['llm_summary'], dict):
            raise ValueError(f"LLMAlertSummaryAgent 'llm_summary' must be a dict, got {type(data['llm_summary']).__name__}")
        
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
    

    
    def _validate_llm_resolution_output(self, data: Any) -> Dict:
        """
        Validate LLMResolutionAgent output structure.
        
        Args:
            data: Output from LLMResolutionAgent
            
        Returns:
            Dict: Validated output with resolution_plans and llm_resolution_summary
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"LLMResolutionAgent must return a dict, got {type(data).__name__}")
        
        required_fields = ['resolution_plans', 'llm_resolution_summary']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"LLMResolutionAgent output missing required fields: {missing_fields}")
        
        if not isinstance(data['resolution_plans'], list):
            raise ValueError(f"LLMResolutionAgent 'resolution_plans' must be a list, got {type(data['resolution_plans']).__name__}")
        
        if not isinstance(data['llm_resolution_summary'], dict):
            raise ValueError(f"LLMResolutionAgent 'llm_resolution_summary' must be a dict, got {type(data['llm_resolution_summary']).__name__}")
        
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
    
    def _validate_governance_output(self, data: Any) -> Dict:
        """
        Validate LLMGovernanceAgent output structure.
        
        Args:
            data: Output from LLMGovernanceAgent
            
        Returns:
            Dict: Validated output with audit_summary and governance_analysis
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"LLMGovernanceAgent must return a dict, got {type(data).__name__}")
        
        required_fields = ['audit_summary', 'governance_analysis']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"LLMGovernanceAgent output missing required fields: {missing_fields}")
        
        if not isinstance(data['governance_analysis'], dict):
            raise ValueError(f"LLMGovernanceAgent 'governance_analysis' must be a dict, got {type(data['governance_analysis']).__name__}")
        
        # Validate governance_analysis structure
        analysis = data['governance_analysis']
        required_analysis_fields = ['risk', 'escalation', 'compliance_issues', 'commentary']
        missing_analysis_fields = [field for field in required_analysis_fields if field not in analysis]
        if missing_analysis_fields:
            raise ValueError(f"Governance analysis missing required fields: {missing_analysis_fields}")
        
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
            
            # Stage 2: LLM Alert Summary (depends on Monitor output)
            self._log_stage('LLMAlertSummaryAgent', 'started')
            llm_output = self.agents['llm_summary'].run(alerts)
            llm_output = self._validate_llm_summary_output(llm_output)
            self._log_stage('LLMAlertSummaryAgent', 'completed', len(llm_output['alerts']))
            
            # Stage 3: Triage (depends on LLM Summary output - extract alerts)
            self._log_stage('TriageAgent', 'started')
            triaged = self.agents['triage'].run(llm_output['alerts'])
            triaged = self._validate_triage_output(triaged)
            self._log_stage('TriageAgent', 'completed', len(triaged))
            
            # Stage 4: LLM Resolution (depends on Triage output)
            self._log_stage('LLMResolutionAgent', 'started')
            llm_resolution_output = self.agents['llm_resolution'].run(triaged)
            llm_resolution_output = self._validate_llm_resolution_output(llm_resolution_output)
            self._log_stage('LLMResolutionAgent', 'completed', len(llm_resolution_output['resolution_plans']))
            
            # Stage 5: OpsLog (depends on LLM Resolution output - extract resolution_plans)
            self._log_stage('OpsLogAgent', 'started')
            summary = self.agents['opslog'].run(llm_resolution_output['resolution_plans'])
            summary = self._validate_opslog_output(summary)
            self._log_stage('OpsLogAgent', 'completed', summary.get('count', 0))
            
            # Stage 6: Governance (depends on OpsLog output)
            self._log_stage('LLMGovernanceAgent', 'started')
            governance_output = self.agents['governance'].run(summary)
            governance_output = self._validate_governance_output(governance_output)
            self._log_stage('LLMGovernanceAgent', 'completed', 1)
            
            # Pipeline complete
            print(f"\n{'='*60}")
            print(f"✅ Pipeline completed successfully")
            print(f"{'='*60}")
            print(f"Audit Summary: {summary}")
            print(f"Governance Analysis:")
            print(f"  Risk Level: {governance_output['governance_analysis']['risk']}")
            print(f"  Escalation: {governance_output['governance_analysis']['escalation']}")
            if governance_output['governance_analysis']['compliance_issues']:
                print(f"  Compliance Issues: {governance_output['governance_analysis']['compliance_issues']}")
            
            return governance_output
            
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
