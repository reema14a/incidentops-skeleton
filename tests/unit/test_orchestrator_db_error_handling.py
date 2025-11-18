"""
Unit tests for orchestrator DB error handling.

Tests that DB write failures are logged and tracked but do not abort pipeline execution.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from orchestrator.orchestrator import PipelineExecutor


class TestOrchestratorDBErrorHandling(unittest.TestCase):
    """Test DB error handling in the orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = PipelineExecutor()
        
        # Mock all agents to return valid data
        self.executor.agents['monitor'].run = Mock(return_value=[
            {'timestamp': '2025-11-18T10:00:00', 'level': 'ERROR', 'message': 'Test alert'}
        ])
        
        self.executor.agents['llm_summary'].run = Mock(return_value={
            'alerts': [{'timestamp': '2025-11-18T10:00:00', 'level': 'ERROR', 'message': 'Test alert'}],
            'llm_summary': {'summary': 'Test summary'}
        })
        
        self.executor.agents['triage'].run = Mock(return_value=[
            {'timestamp': '2025-11-18T10:00:00', 'level': 'ERROR', 'message': 'Test alert', 
             'severity': 'high', 'category': 'system'}
        ])
        
        self.executor.agents['llm_resolution'].run = Mock(return_value={
            'resolution_plans': [{'alert': 'Test', 'resolution': 'Fix it'}],
            'llm_resolution_summary': {'summary': 'Resolution summary'}
        })
        
        self.executor.agents['opslog'].run = Mock(return_value={
            'status': 'completed',
            'count': 1,
            'timestamp': '2025-11-18T10:00:00'
        })
        
        self.executor.agents['governance'].run = Mock(return_value={
            'audit_summary': {'status': 'completed', 'count': 1, 'timestamp': '2025-11-18T10:00:00'},
            'governance_analysis': {
                'risk': 'medium',
                'escalation': 'not_required',
                'compliance_issues': [],
                'commentary': 'All good'
            }
        })
        
        self.executor.agents['notification'].run = Mock(return_value={
            'governance_output': {},
            'notification_status': 'success',
            'notifications_sent': [
                {'channel': 'pushover', 'status': 'success', 'response': 'OK'}
            ]
        })
    
    @patch('orchestrator.orchestrator.db_util')
    def test_pipeline_continues_when_initial_db_write_fails(self, mock_db_util):
        """Test that pipeline continues when insert_pipeline_run fails."""
        # Mock insert_pipeline_run to return None (failure)
        mock_db_util.insert_pipeline_run.return_value = None
        mock_db_util.insert_audit_summary.return_value = False
        mock_db_util.insert_governance_analysis.return_value = False
        mock_db_util.insert_compliance_issues.return_value = False
        mock_db_util.insert_notification_event.return_value = False
        
        # Execute pipeline
        result = self.executor.run()
        
        # Verify pipeline completed
        self.assertIsNotNone(result)
        self.assertEqual(result['notification_status'], 'success')
        
        # Verify DB write status shows failures
        self.assertIn('db_write_status', result)
        self.assertFalse(result['db_write_status']['pipeline_run'])
        self.assertFalse(result['db_write_status']['audit_summary'])
        self.assertFalse(result['db_write_status']['governance_analysis'])
        self.assertFalse(result['db_write_status']['compliance_issues'])
        self.assertFalse(result['db_write_status']['notification_events'])
        
        # Verify run_id is None
        self.assertIsNone(result['run_id'])
    
    @patch('orchestrator.orchestrator.db_util')
    def test_pipeline_continues_when_audit_summary_write_fails(self, mock_db_util):
        """Test that pipeline continues when insert_audit_summary fails."""
        # Mock successful pipeline_run creation but failed audit_summary
        mock_db_util.insert_pipeline_run.return_value = 123
        mock_db_util.insert_audit_summary.return_value = False
        mock_db_util.insert_governance_analysis.return_value = True
        mock_db_util.insert_compliance_issues.return_value = True
        mock_db_util.insert_notification_event.return_value = True
        mock_db_util.get_connection.return_value.__enter__ = Mock()
        mock_db_util.get_connection.return_value.__exit__ = Mock()
        
        # Execute pipeline
        result = self.executor.run()
        
        # Verify pipeline completed
        self.assertIsNotNone(result)
        self.assertEqual(result['notification_status'], 'success')
        
        # Verify DB write status
        self.assertIn('db_write_status', result)
        self.assertTrue(result['db_write_status']['pipeline_run'])
        self.assertFalse(result['db_write_status']['audit_summary'])
        self.assertTrue(result['db_write_status']['governance_analysis'])
        self.assertTrue(result['db_write_status']['compliance_issues'])
        self.assertTrue(result['db_write_status']['notification_events'])
        
        # Verify run_id is set
        self.assertEqual(result['run_id'], 123)
    
    @patch('orchestrator.orchestrator.db_util')
    def test_pipeline_continues_when_governance_write_fails(self, mock_db_util):
        """Test that pipeline continues when governance writes fail."""
        # Mock successful pipeline_run and audit_summary but failed governance
        mock_db_util.insert_pipeline_run.return_value = 456
        mock_db_util.insert_audit_summary.return_value = True
        mock_db_util.insert_governance_analysis.return_value = False
        mock_db_util.insert_compliance_issues.return_value = False
        mock_db_util.insert_notification_event.return_value = True
        mock_db_util.get_connection.return_value.__enter__ = Mock()
        mock_db_util.get_connection.return_value.__exit__ = Mock()
        
        # Execute pipeline
        result = self.executor.run()
        
        # Verify pipeline completed
        self.assertIsNotNone(result)
        self.assertEqual(result['notification_status'], 'success')
        
        # Verify DB write status
        self.assertIn('db_write_status', result)
        self.assertTrue(result['db_write_status']['pipeline_run'])
        self.assertTrue(result['db_write_status']['audit_summary'])
        self.assertFalse(result['db_write_status']['governance_analysis'])
        self.assertFalse(result['db_write_status']['compliance_issues'])
        self.assertTrue(result['db_write_status']['notification_events'])
    
    @patch('orchestrator.orchestrator.db_util')
    def test_pipeline_continues_when_notification_write_fails(self, mock_db_util):
        """Test that pipeline continues when notification event writes fail."""
        # Mock all successful except notification_events
        mock_db_util.insert_pipeline_run.return_value = 789
        mock_db_util.insert_audit_summary.return_value = True
        mock_db_util.insert_governance_analysis.return_value = True
        mock_db_util.insert_compliance_issues.return_value = True
        mock_db_util.insert_notification_event.return_value = False
        mock_db_util.get_connection.return_value.__enter__ = Mock()
        mock_db_util.get_connection.return_value.__exit__ = Mock()
        
        # Execute pipeline
        result = self.executor.run()
        
        # Verify pipeline completed
        self.assertIsNotNone(result)
        self.assertEqual(result['notification_status'], 'success')
        
        # Verify DB write status
        self.assertIn('db_write_status', result)
        self.assertTrue(result['db_write_status']['pipeline_run'])
        self.assertTrue(result['db_write_status']['audit_summary'])
        self.assertTrue(result['db_write_status']['governance_analysis'])
        self.assertTrue(result['db_write_status']['compliance_issues'])
        self.assertFalse(result['db_write_status']['notification_events'])
    
    @patch('orchestrator.orchestrator.db_util')
    def test_pipeline_continues_when_db_raises_exception(self, mock_db_util):
        """Test that pipeline continues when DB operations raise exceptions."""
        # Mock insert_pipeline_run to raise an exception
        mock_db_util.insert_pipeline_run.side_effect = Exception("Database connection failed")
        mock_db_util.insert_audit_summary.side_effect = Exception("Database error")
        mock_db_util.insert_governance_analysis.side_effect = Exception("Database error")
        mock_db_util.insert_compliance_issues.side_effect = Exception("Database error")
        mock_db_util.insert_notification_event.side_effect = Exception("Database error")
        
        # Execute pipeline
        result = self.executor.run()
        
        # Verify pipeline completed despite exceptions
        self.assertIsNotNone(result)
        self.assertEqual(result['notification_status'], 'success')
        
        # Verify all DB write statuses are False
        self.assertIn('db_write_status', result)
        self.assertFalse(result['db_write_status']['pipeline_run'])
        self.assertFalse(result['db_write_status']['audit_summary'])
        self.assertFalse(result['db_write_status']['governance_analysis'])
        self.assertFalse(result['db_write_status']['compliance_issues'])
        self.assertFalse(result['db_write_status']['notification_events'])
    
    @patch('orchestrator.orchestrator.db_util')
    def test_all_db_writes_successful(self, mock_db_util):
        """Test that db_write_status correctly reflects all successful writes."""
        # Mock all DB operations as successful
        mock_db_util.insert_pipeline_run.return_value = 999
        mock_db_util.insert_audit_summary.return_value = True
        mock_db_util.insert_governance_analysis.return_value = True
        mock_db_util.insert_compliance_issues.return_value = True
        mock_db_util.insert_notification_event.return_value = True
        mock_db_util.get_connection.return_value.__enter__ = Mock()
        mock_db_util.get_connection.return_value.__exit__ = Mock()
        
        # Execute pipeline
        result = self.executor.run()
        
        # Verify pipeline completed
        self.assertIsNotNone(result)
        self.assertEqual(result['notification_status'], 'success')
        
        # Verify all DB write statuses are True
        self.assertIn('db_write_status', result)
        self.assertTrue(result['db_write_status']['pipeline_run'])
        self.assertTrue(result['db_write_status']['audit_summary'])
        self.assertTrue(result['db_write_status']['governance_analysis'])
        self.assertTrue(result['db_write_status']['compliance_issues'])
        self.assertTrue(result['db_write_status']['notification_events'])
        
        # Verify run_id is set
        self.assertEqual(result['run_id'], 999)


if __name__ == '__main__':
    unittest.main()
