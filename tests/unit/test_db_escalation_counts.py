"""
Unit tests for get_escalation_text_counts() database utility function.
"""
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch
from db.db_util import get_escalation_text_counts, insert_pipeline_run, insert_governance_analysis


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Mock the settings to use the temp database
    with patch('db.db_util._get_db_path', return_value=path):
        # Initialize the database
        from db.db_util import initialize_database
        initialize_database()
        
        yield path
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


def test_get_escalation_text_counts_empty_database(temp_db):
    """Test get_escalation_text_counts with an empty database."""
    with patch('db.db_util._get_db_path', return_value=temp_db):
        result = get_escalation_text_counts()
        
        assert isinstance(result, dict)
        assert len(result) == 0


def test_get_escalation_text_counts_single_escalation(temp_db):
    """Test get_escalation_text_counts with a single escalation entry."""
    with patch('db.db_util._get_db_path', return_value=temp_db):
        # Insert a pipeline run
        run_id = insert_pipeline_run(
            timestamp="2025-11-19T10:00:00.000000",
            alerts_count=5
        )
        
        # Insert governance analysis with escalation
        insert_governance_analysis(
            run_id=run_id,
            gov_dict={
                'risk': 'medium',
                'escalation': 'Monitor for recurring patterns',
                'commentary': 'Test commentary'
            }
        )
        
        # Get escalation counts
        result = get_escalation_text_counts()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert result['Monitor for recurring patterns'] == 1


def test_get_escalation_text_counts_multiple_same_escalation(temp_db):
    """Test get_escalation_text_counts with multiple runs having the same escalation."""
    with patch('db.db_util._get_db_path', return_value=temp_db):
        escalation_text = 'None required'
        
        # Insert multiple pipeline runs with the same escalation
        for i in range(3):
            run_id = insert_pipeline_run(
                timestamp=f"2025-11-19T10:{i:02d}:00.000000",
                alerts_count=0
            )
            
            insert_governance_analysis(
                run_id=run_id,
                gov_dict={
                    'risk': 'low',
                    'escalation': escalation_text,
                    'commentary': f'Test commentary {i}'
                }
            )
        
        # Get escalation counts
        result = get_escalation_text_counts()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert result[escalation_text] == 3


def test_get_escalation_text_counts_multiple_different_escalations(temp_db):
    """Test get_escalation_text_counts with multiple different escalation types."""
    with patch('db.db_util._get_db_path', return_value=temp_db):
        escalations = [
            'None required',
            'Monitor for recurring patterns',
            'Review with team lead if issues persist',
            'Escalate to on-call engineer',
            'None required',  # Duplicate
            'Monitor for recurring patterns',  # Duplicate
        ]
        
        # Insert pipeline runs with different escalations
        for i, escalation_text in enumerate(escalations):
            run_id = insert_pipeline_run(
                timestamp=f"2025-11-19T10:{i:02d}:00.000000",
                alerts_count=i
            )
            
            insert_governance_analysis(
                run_id=run_id,
                gov_dict={
                    'risk': 'medium',
                    'escalation': escalation_text,
                    'commentary': f'Test commentary {i}'
                }
            )
        
        # Get escalation counts
        result = get_escalation_text_counts()
        
        assert isinstance(result, dict)
        assert len(result) == 4
        assert result['None required'] == 2
        assert result['Monitor for recurring patterns'] == 2
        assert result['Review with team lead if issues persist'] == 1
        assert result['Escalate to on-call engineer'] == 1


def test_get_escalation_text_counts_ignores_null_and_empty(temp_db):
    """Test that get_escalation_text_counts ignores NULL and empty escalation values."""
    with patch('db.db_util._get_db_path', return_value=temp_db):
        # Insert pipeline runs with NULL and empty escalations
        run_id1 = insert_pipeline_run(
            timestamp="2025-11-19T10:00:00.000000",
            alerts_count=1
        )
        
        run_id2 = insert_pipeline_run(
            timestamp="2025-11-19T10:01:00.000000",
            alerts_count=2
        )
        
        run_id3 = insert_pipeline_run(
            timestamp="2025-11-19T10:02:00.000000",
            alerts_count=3
        )
        
        # Insert governance with NULL escalation (by not including it)
        insert_governance_analysis(
            run_id=run_id1,
            gov_dict={
                'risk': 'low',
                'commentary': 'Test commentary'
            }
        )
        
        # Insert governance with empty string escalation
        insert_governance_analysis(
            run_id=run_id2,
            gov_dict={
                'risk': 'medium',
                'escalation': '',
                'commentary': 'Test commentary'
            }
        )
        
        # Insert governance with valid escalation
        insert_governance_analysis(
            run_id=run_id3,
            gov_dict={
                'risk': 'high',
                'escalation': 'Escalate to on-call engineer',
                'commentary': 'Test commentary'
            }
        )
        
        # Get escalation counts
        result = get_escalation_text_counts()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert result['Escalate to on-call engineer'] == 1


def test_get_escalation_text_counts_with_special_characters(temp_db):
    """Test get_escalation_text_counts with escalation text containing special characters."""
    with patch('db.db_util._get_db_path', return_value=temp_db):
        escalation_text = "Escalate immediately - critical issue detected!"
        
        run_id = insert_pipeline_run(
            timestamp="2025-11-19T10:00:00.000000",
            alerts_count=10
        )
        
        insert_governance_analysis(
            run_id=run_id,
            gov_dict={
                'risk': 'critical',
                'escalation': escalation_text,
                'commentary': 'Test commentary'
            }
        )
        
        # Get escalation counts
        result = get_escalation_text_counts()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert result[escalation_text] == 1
