"""
Tests for orchestrator pipeline execution and data flow validation.
"""
import unittest
from unittest.mock import Mock, patch
from orchestrator.orchestrator import PipelineExecutor


class TestPipelineExecutor(unittest.TestCase):
    """Test cases for PipelineExecutor strict sequential data flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = PipelineExecutor()
    
    def test_validate_monitor_output_valid(self):
        """Test that valid monitor output passes validation."""
        valid_alerts = [
            {
                'timestamp': '2025-11-15 10:00:00',
                'level': 'ERROR',
                'message': 'Database connection failed',
                'line_number': 1
            }
        ]
        result = self.executor._validate_monitor_output(valid_alerts)
        self.assertEqual(result, valid_alerts)
    
    def test_validate_monitor_output_invalid_type(self):
        """Test that invalid monitor output type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.executor._validate_monitor_output("not a list")
        self.assertIn("must return a list", str(context.exception))
    
    def test_validate_monitor_output_missing_fields(self):
        """Test that monitor output with missing fields raises ValueError."""
        invalid_alerts = [
            {'timestamp': '2025-11-15 10:00:00'}  # Missing 'level' and 'message'
        ]
        with self.assertRaises(ValueError) as context:
            self.executor._validate_monitor_output(invalid_alerts)
        self.assertIn("missing required fields", str(context.exception))
    
    def test_validate_llm_summary_output_valid(self):
        """Test that valid LLM summary output passes validation."""
        valid_output = {
            'alerts': [
                {
                    'timestamp': '2025-11-15 10:00:00',
                    'level': 'ERROR',
                    'message': 'Database connection failed'
                }
            ],
            'llm_summary': {
                'summary': 'Test summary',
                'categories': ['Database'],
                'severity_breakdown': {'ERROR': 1},
                'root_causes': ['Connection issue']
            }
        }
        result = self.executor._validate_llm_summary_output(valid_output)
        self.assertEqual(result, valid_output)
    
    def test_validate_llm_summary_output_invalid_type(self):
        """Test that invalid LLM summary output type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.executor._validate_llm_summary_output([])
        self.assertIn("must return a dict", str(context.exception))
    
    def test_validate_llm_summary_output_missing_fields(self):
        """Test that LLM summary output with missing fields raises ValueError."""
        invalid_output = {
            'alerts': []
            # Missing 'llm_summary'
        }
        with self.assertRaises(ValueError) as context:
            self.executor._validate_llm_summary_output(invalid_output)
        self.assertIn("missing required fields", str(context.exception))
    
    def test_validate_llm_summary_output_invalid_alerts_type(self):
        """Test that LLM summary output with non-list alerts raises ValueError."""
        invalid_output = {
            'alerts': 'not a list',
            'llm_summary': {}
        }
        with self.assertRaises(ValueError) as context:
            self.executor._validate_llm_summary_output(invalid_output)
        self.assertIn("'alerts' must be a list", str(context.exception))
    
    def test_validate_triage_output_valid(self):
        """Test that valid triage output passes validation."""
        valid_triaged = [
            {
                'timestamp': '2025-11-15 10:00:00',
                'level': 'ERROR',
                'message': 'Database connection failed',
                'severity': 'high',
                'category': 'database'
            }
        ]
        result = self.executor._validate_triage_output(valid_triaged)
        self.assertEqual(result, valid_triaged)
    
    def test_validate_triage_output_missing_severity(self):
        """Test that triage output without severity raises ValueError."""
        invalid_triaged = [
            {
                'timestamp': '2025-11-15 10:00:00',
                'level': 'ERROR',
                'message': 'Database connection failed',
                'category': 'database'
            }
        ]
        with self.assertRaises(ValueError) as context:
            self.executor._validate_triage_output(invalid_triaged)
        self.assertIn("missing required fields", str(context.exception))
        self.assertIn("severity", str(context.exception))
    
    def test_validate_resolution_output_valid(self):
        """Test that valid resolution output passes validation."""
        valid_plans = [
            {
                'alert_id': 'test_123',
                'severity': 'high',
                'category': 'database',
                'recommended_actions': ['Restart database', 'Check logs']
            }
        ]
        result = self.executor._validate_resolution_output(valid_plans)
        self.assertEqual(result, valid_plans)
    
    def test_validate_resolution_output_invalid_actions(self):
        """Test that resolution output with non-list actions raises ValueError."""
        invalid_plans = [
            {
                'alert_id': 'test_123',
                'severity': 'high',
                'category': 'database',
                'recommended_actions': 'not a list'
            }
        ]
        with self.assertRaises(ValueError) as context:
            self.executor._validate_resolution_output(invalid_plans)
        self.assertIn("must be a list", str(context.exception))
    
    def test_validate_opslog_output_valid(self):
        """Test that valid opslog output passes validation."""
        valid_summary = {
            'status': 'logged',
            'count': 4,
            'timestamp': '2025-11-15 10:00:00'
        }
        result = self.executor._validate_opslog_output(valid_summary)
        self.assertEqual(result, valid_summary)
    
    def test_validate_opslog_output_invalid_type(self):
        """Test that opslog output with wrong type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.executor._validate_opslog_output([])
        self.assertIn("must return a dict", str(context.exception))
    
    @patch('orchestrator.orchestrator.MonitorAgent')
    @patch('orchestrator.orchestrator.LLMAlertSummaryAgent')
    @patch('orchestrator.orchestrator.TriageAgent')
    @patch('orchestrator.orchestrator.ResolutionAgent')
    @patch('orchestrator.orchestrator.LLMResolutionAgent')
    @patch('orchestrator.orchestrator.OpsLogAgent')
    @patch('orchestrator.orchestrator.LLMGovernanceAgent')
    def test_pipeline_sequential_execution(self, mock_governance, mock_opslog, mock_llm_resolution, mock_resolution, mock_triage, mock_llm_summary, mock_monitor):
        """Test that pipeline executes agents in strict sequential order."""
        # Setup mock return values
        mock_monitor_instance = Mock()
        mock_monitor_instance.run.return_value = [
            {'timestamp': '2025-11-15 10:00:00', 'level': 'ERROR', 'message': 'Test error'}
        ]
        mock_monitor.return_value = mock_monitor_instance
        
        mock_llm_summary_instance = Mock()
        mock_llm_summary_instance.run.return_value = {
            'alerts': [
                {'timestamp': '2025-11-15 10:00:00', 'level': 'ERROR', 'message': 'Test error'}
            ],
            'llm_summary': {
                'summary': 'Test summary',
                'categories': ['General'],
                'severity_breakdown': {'ERROR': 1},
                'root_causes': ['Test cause']
            }
        }
        mock_llm_summary.return_value = mock_llm_summary_instance
        
        mock_triage_instance = Mock()
        mock_triage_instance.run.return_value = [
            {
                'timestamp': '2025-11-15 10:00:00',
                'level': 'ERROR',
                'message': 'Test error',
                'severity': 'high',
                'category': 'general'
            }
        ]
        mock_triage.return_value = mock_triage_instance
        
        mock_resolution_instance = Mock()
        mock_resolution_instance.run.return_value = [
            {
                'alert_id': 'test_123',
                'severity': 'high',
                'category': 'general',
                'recommended_actions': ['Action 1']
            }
        ]
        mock_resolution.return_value = mock_resolution_instance
        
        mock_llm_resolution_instance = Mock()
        mock_llm_resolution_instance.run.return_value = {
            'resolution_plans': [
                {
                    'alert_id': 'test_123',
                    'severity': 'high',
                    'category': 'general',
                    'recommended_actions': ['Action 1']
                }
            ],
            'llm_resolution_summary': {
                'summary': 'Test resolution summary',
                'recommendations': ['Recommendation 1'],
                'escalation': 'No escalation required',
                'affected_systems': ['System 1']
            }
        }
        mock_llm_resolution.return_value = mock_llm_resolution_instance
        
        mock_opslog_instance = Mock()
        mock_opslog_instance.run.return_value = {
            'status': 'logged',
            'count': 1,
            'timestamp': '2025-11-15 10:00:00'
        }
        mock_opslog.return_value = mock_opslog_instance
        
        mock_governance_instance = Mock()
        mock_governance_instance.run.return_value = {
            'audit_summary': {
                'status': 'logged',
                'count': 1,
                'timestamp': '2025-11-15 10:00:00'
            },
            'governance_analysis': {
                'risk': 'low',
                'escalation': 'No escalation required',
                'compliance_issues': [],
                'commentary': 'Test commentary'
            }
        }
        mock_governance.return_value = mock_governance_instance
        
        # Execute pipeline
        executor = PipelineExecutor()
        result = executor.run()
        
        # Verify sequential execution
        mock_monitor_instance.run.assert_called_once()
        mock_llm_summary_instance.run.assert_called_once()
        mock_triage_instance.run.assert_called_once()
        mock_resolution_instance.run.assert_called_once()
        mock_llm_resolution_instance.run.assert_called_once()
        mock_opslog_instance.run.assert_called_once()
        mock_governance_instance.run.assert_called_once()
        
        # Verify result structure (now returns governance output)
        self.assertIn('audit_summary', result)
        self.assertIn('governance_analysis', result)
        self.assertEqual(result['audit_summary']['status'], 'logged')
        self.assertEqual(result['audit_summary']['count'], 1)
        self.assertEqual(result['governance_analysis']['risk'], 'low')


if __name__ == '__main__':
    unittest.main()
