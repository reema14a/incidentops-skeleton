"""
Temporary test to verify JSON storage in audit_summary and governance_analysis tables.
"""
import json
import tempfile
import os
import shutil
import importlib

import pytest


@pytest.fixture(autouse=True)
def isolated_temp_db(monkeypatch):
    """
    Ensures every test gets its own isolated temp DB before db_util is imported.
    """
    # Create temp folder + DB path
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_incidents.db")

    # Tell db_util to use this DB path
    monkeypatch.setenv("DB_PATH", temp_db)

    # Now re-import db_util after env var is set
    import db.db_util as db_util
    importlib.reload(db_util)

    # Initialize database
    db_util.initialize_database()

    yield db_util  # provide the reloaded, correct version

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_audit_summary_json_storage(isolated_temp_db):
    db_util = isolated_temp_db

    run_id = db_util.insert_pipeline_run("2025-11-18T10:30:00", 5, "test_data.txt")
    assert run_id is not None

    audit_dict = {
        "status": "completed",
        "count": 5,
        "timestamp": "2025-11-18T10:30:00",
        "extra_field_1": "some_value",
        "extra_field_2": {"nested": "data"},
        "extra_field_3": [1, 2, 3]
    }

    success = db_util.insert_audit_summary(run_id, audit_dict)
    assert success is True

    with db_util.get_connection() as conn:
        row = conn.execute(
            "SELECT audit_data FROM audit_summary WHERE run_id = ?",
            (run_id,)
        ).fetchone()

        assert row is not None
        stored_data = json.loads(row["audit_data"])
        assert stored_data == audit_dict


def test_governance_analysis_json_storage(isolated_temp_db):
    db_util = isolated_temp_db

    run_id = db_util.insert_pipeline_run("2025-11-18T11:00:00", 3, "test_data2.txt")
    assert run_id is not None

    gov_dict = {
        "risk": "high",
        "escalation": "immediate",
        "escalation_category": "immediate",
        "commentary": "Critical issues detected",
        "compliance_issues": ["Issue 1", "Issue 2"],
        "extra_metadata": {"analyst": "John Doe", "reviewed": True},
        "score": 85
    }

    success = db_util.insert_governance_analysis(run_id, gov_dict)
    assert success is True

    with db_util.get_connection() as conn:
        row = conn.execute(
            "SELECT governance_data FROM governance_analysis WHERE run_id = ?",
            (run_id,)
        ).fetchone()

        assert row is not None
        stored_data = json.loads(row["governance_data"])

        assert stored_data == gov_dict
