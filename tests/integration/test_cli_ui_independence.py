"""
Integration test to verify CLI and UI pipeline execution independence.

This test ensures that:
1. CLI pipeline execution works via console_client
2. UI pipeline execution works via Pipeline_Runner
3. Both paths use the same orchestrator without conflicts
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_cli_execution_works():
    """Test that CLI pipeline execution works independently."""
    from ui.console_client import run
    from orchestrator.orchestrator import run_pipeline
    
    # Mock the pipeline to avoid actual execution
    with patch('orchestrator.orchestrator.PipelineExecutor') as mock_executor:
        mock_instance = MagicMock()
        mock_executor.return_value = mock_instance
        
        # Mock successful pipeline output (matches NotificationAgent output structure)
        mock_output = {
            'governance_output': {
                'governance_analysis': {
                    'risk': 'low',
                    'escalation': 'none',
                    'compliance_issues': [],
                    'commentary': 'Test commentary'
                },
                'audit_summary': {
                    'status': 'success',
                    'count': 5,
                    'timestamp': '2024-01-15T10:00:00'
                }
            },
            'notification_status': 'sent',
            'notifications_sent': []
        }
        mock_instance.run.return_value = mock_output
        
        # Execute CLI pipeline in test mode
        result = run(test_mode=True)
        
        # Verify execution
        assert result is not None
        assert isinstance(result, dict)
        assert mock_instance.run.called
        print("✓ CLI execution test passed")


def test_ui_execution_works():
    """Test that UI pipeline execution works independently."""
    from ui.pages.Pipeline_Runner import run_pipeline_with_input
    
    # Mock the pipeline to avoid actual execution
    with patch('ui.pages.Pipeline_Runner.run_pipeline') as mock_pipeline:
        # Mock successful pipeline output (matches NotificationAgent output structure)
        mock_output = {
            'governance_output': {
                'governance_analysis': {
                    'risk': 'medium',
                    'escalation': 'review',
                    'compliance_issues': ['issue1'],
                    'commentary': 'Test commentary'
                },
                'audit_summary': {
                    'status': 'success',
                    'count': 3,
                    'timestamp': '2024-01-15T11:00:00'
                }
            },
            'notification_status': 'sent',
            'notifications_sent': [
                {'channel': 'gmail', 'status': 'success'}
            ]
        }
        mock_pipeline.return_value = mock_output
        
        # Execute UI pipeline
        result = run_pipeline_with_input(log_text="test log data")
        
        # Verify execution
        assert result is not None
        assert isinstance(result, dict)
        assert result['status'] == 'success'
        assert 'final_output' in result
        assert mock_pipeline.called
        print("✓ UI execution test passed")


def test_both_use_same_orchestrator():
    """Test that both CLI and UI use the same orchestrator module."""
    from ui.console_client import run_pipeline as cli_pipeline
    from ui.pages.Pipeline_Runner import run_pipeline as ui_pipeline
    
    # Both should import from the same orchestrator module
    assert cli_pipeline.__module__ == 'orchestrator.orchestrator'
    assert ui_pipeline.__module__ == 'orchestrator.orchestrator'
    
    # Both should be the same function
    assert cli_pipeline is ui_pipeline
    print("✓ Shared orchestrator test passed")


def test_cli_does_not_import_streamlit():
    """Test that CLI execution doesn't require Streamlit."""
    import sys
    
    # Temporarily hide streamlit from imports
    original_streamlit = sys.modules.get('streamlit')
    if 'streamlit' in sys.modules:
        del sys.modules['streamlit']
    
    try:
        # CLI should work without streamlit
        from ui.console_client import run
        from orchestrator.orchestrator import run_pipeline
        
        # Verify imports work
        assert run is not None
        assert run_pipeline is not None
        print("✓ CLI independence from Streamlit test passed")
        
    finally:
        # Restore streamlit if it was there
        if original_streamlit:
            sys.modules['streamlit'] = original_streamlit


if __name__ == '__main__':
    print("Testing CLI and UI pipeline execution independence...\n")
    
    test_cli_execution_works()
    test_ui_execution_works()
    test_both_use_same_orchestrator()
    test_cli_does_not_import_streamlit()
    
    print("\n✅ All independence tests passed!")
    print("CLI and UI can execute pipelines independently without conflicts.")
