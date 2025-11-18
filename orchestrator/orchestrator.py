"""
Orchestrator module for IncidentOps pipeline execution.

This module ensures strict sequential data flow across all agents:
1. MonitorAgent → alerts (list of dicts with timestamp, level, message)
2. LLMAlertSummaryAgent → enriched alerts with LLM summary
3. TriageAgent → triaged alerts (adds severity, category)
4. LLMResolutionAgent → resolution plans with LLM-generated recommendations and summary
5. OpsLogAgent → audit summary (dict with status, count, timestamp)
6. LLMGovernanceAgent → governance analysis (risk scoring, escalation, compliance)
7. NotificationAgent → notification delivery status (sends alerts via MCP)

Each stage validates input/output data structures to prevent invalid data flow.
Pipeline execution stops immediately if any validation fails.
"""
from typing import Any, List, Dict, Optional
import logging
from datetime import datetime
from agents.monitor_agent import MonitorAgent
from agents.llm_alert_summary_agent import LLMAlertSummaryAgent
from agents.triage_agent import TriageAgent
from agents.llm_resolution_agent import LLMResolutionAgent
from agents.opslog_agent import OpsLogAgent
from agents.llm_governance_agent import LLMGovernanceAgent
from agents.notification_agent import NotificationAgent
from db import db_util

logger = logging.getLogger(__name__)


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
            'governance': LLMGovernanceAgent("LLMGovernanceAgent"),
            'notification': NotificationAgent("NotificationAgent")
        }
        self.execution_log = []
        self.run_id: Optional[int] = None
        self.db_write_status = {
            'pipeline_run': False,
            'audit_summary': False,
            'governance_analysis': False,
            'compliance_issues': False,
            'notification_events': False
        }
    
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
    
    def _validate_notification_output(self, data: Any) -> Dict:
        """
        Validate NotificationAgent output structure.
        
        Args:
            data: Output from NotificationAgent
            
        Returns:
            Dict: Validated output with governance_output, notification_status, and notifications_sent
            
        Raises:
            ValueError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"NotificationAgent must return a dict, got {type(data).__name__}")
        
        required_fields = ['governance_output', 'notification_status', 'notifications_sent']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"NotificationAgent output missing required fields: {missing_fields}")
        
        if not isinstance(data['notifications_sent'], list):
            raise ValueError(f"NotificationAgent 'notifications_sent' must be a list, got {type(data['notifications_sent']).__name__}")
        
        return data
    
    def run(self) -> Dict:
        """
        Execute the complete pipeline with strict sequential data flow.
        
        Returns:
            Dict: Pipeline execution summary with db_write_status
            
        Raises:
            Exception: If any stage fails or data validation fails
        """
        try:
            # Create pipeline_runs entry at pipeline start
            timestamp = datetime.utcnow().isoformat()
            try:
                self.run_id = db_util.insert_pipeline_run(
                    timestamp=timestamp,
                    alerts_count=0,  # Will be updated after Monitor stage
                    raw_data_path=None
                )
                
                if self.run_id:
                    self.db_write_status['pipeline_run'] = True
                    logger.info(f"Created pipeline run record with ID: {self.run_id}")
                else:
                    self.db_write_status['pipeline_run'] = False
                    logger.error("Failed to create pipeline run record - continuing without DB persistence")
            except Exception as e:
                self.db_write_status['pipeline_run'] = False
                logger.error(f"Exception while creating pipeline run record: {e} - continuing without DB persistence")
            
            # Stage 1: Monitor
            self._log_stage('MonitorAgent', 'started')
            alerts = self.agents['monitor'].run()
            alerts = self._validate_monitor_output(alerts)
            self._log_stage('MonitorAgent', 'completed', len(alerts))
            
            # Update pipeline_runs with actual alerts_count
            if self.run_id:
                try:
                    with db_util.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE pipeline_runs 
                            SET alerts_count = ? 
                            WHERE id = ?
                        """, (len(alerts), self.run_id))
                        logger.info(f"Updated pipeline run {self.run_id} with alerts_count={len(alerts)}")
                except Exception as e:
                    logger.error(f"Failed to update alerts_count for run_id {self.run_id}: {e}")
                    # Note: This is an update operation, not tracked separately in db_write_status
            
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
            
            # Write audit_summary after OpsLog
            if self.run_id:
                try:
                    success = db_util.insert_audit_summary(self.run_id, summary)
                    self.db_write_status['audit_summary'] = success
                    if not success:
                        logger.error(f"Failed to write audit_summary for run_id {self.run_id}")
                except Exception as e:
                    self.db_write_status['audit_summary'] = False
                    logger.error(f"Exception while writing audit_summary for run_id {self.run_id}: {e}")
            else:
                self.db_write_status['audit_summary'] = False
                logger.warning("Skipping audit_summary write - no valid run_id")
            
            # Stage 6: Governance (depends on OpsLog output)
            self._log_stage('LLMGovernanceAgent', 'started')
            governance_output = self.agents['governance'].run(summary)
            governance_output = self._validate_governance_output(governance_output)
            self._log_stage('LLMGovernanceAgent', 'completed', 1)
            
            # Write governance_analysis and compliance_issues after Governance step
            if self.run_id:
                gov_analysis = governance_output['governance_analysis']
                
                # Insert governance analysis
                try:
                    success = db_util.insert_governance_analysis(self.run_id, gov_analysis)
                    self.db_write_status['governance_analysis'] = success
                    if not success:
                        logger.error(f"Failed to write governance_analysis for run_id {self.run_id}")
                except Exception as e:
                    self.db_write_status['governance_analysis'] = False
                    logger.error(f"Exception while writing governance_analysis for run_id {self.run_id}: {e}")
                
                # Insert compliance issues
                try:
                    compliance_issues = gov_analysis.get('compliance_issues', [])
                    success = db_util.insert_compliance_issues(self.run_id, compliance_issues)
                    self.db_write_status['compliance_issues'] = success
                    if not success:
                        logger.error(f"Failed to write compliance_issues for run_id {self.run_id}")
                except Exception as e:
                    self.db_write_status['compliance_issues'] = False
                    logger.error(f"Exception while writing compliance_issues for run_id {self.run_id}: {e}")
            else:
                self.db_write_status['governance_analysis'] = False
                self.db_write_status['compliance_issues'] = False
                logger.warning("Skipping governance writes - no valid run_id")
            
            # Stage 7: Notification (depends on Governance output)
            self._log_stage('NotificationAgent', 'started')
            notification_output = self.agents['notification'].run(governance_output)
            notification_output = self._validate_notification_output(notification_output)
            self._log_stage('NotificationAgent', 'completed', len(notification_output['notifications_sent']))
            
            # Write notification_events after Notification step
            if self.run_id:
                try:
                    notifications_sent = notification_output.get('notifications_sent', [])
                    
                    # Insert each notification event
                    all_success = True
                    for notification in notifications_sent:
                        try:
                            channel = notification.get('channel', 'unknown')
                            status = notification.get('status', 'unknown')
                            response = str(notification.get('response', ''))
                            
                            success = db_util.insert_notification_event(
                                self.run_id, 
                                channel, 
                                status, 
                                response
                            )
                            if not success:
                                all_success = False
                                logger.error(f"Failed to write notification_event for run_id {self.run_id}, channel {channel}")
                        except Exception as e:
                            all_success = False
                            logger.error(f"Exception while writing notification_event for run_id {self.run_id}: {e}")
                    
                    self.db_write_status['notification_events'] = all_success
                except Exception as e:
                    self.db_write_status['notification_events'] = False
                    logger.error(f"Exception while processing notification_events for run_id {self.run_id}: {e}")
            else:
                self.db_write_status['notification_events'] = False
                logger.warning("Skipping notification_events write - no valid run_id")
            
            # Pipeline complete
            print(f"\n{'='*60}")
            print(f"✅ Pipeline completed successfully")
            print(f"{'='*60}")
            print(f"Pipeline Run ID: {self.run_id}")
            print(f"Audit Summary: {summary}")
            print(f"Governance Analysis:")
            print(f"  Risk Level: {governance_output['governance_analysis']['risk']}")
            print(f"  Escalation: {governance_output['governance_analysis']['escalation']}")
            if governance_output['governance_analysis']['compliance_issues']:
                print(f"  Compliance Issues: {governance_output['governance_analysis']['compliance_issues']}")
            print(f"Notification Status: {notification_output['notification_status']}")
            if notification_output['notifications_sent']:
                print(f"  Notifications Sent: {len(notification_output['notifications_sent'])}")
            
            # Log DB write status
            db_failures = [k for k, v in self.db_write_status.items() if not v]
            if db_failures:
                logger.warning(f"Some DB writes failed: {db_failures}")
                print(f"\n⚠️  Database write failures: {', '.join(db_failures)}")
            else:
                logger.info("All DB writes completed successfully")
                print(f"\n✅ All database writes completed successfully")
            
            # Add DB write status to output
            notification_output['db_write_status'] = self.db_write_status
            notification_output['run_id'] = self.run_id
            
            return notification_output
            
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
