# Orchestrator DB Integration Implementation

## Overview

This document describes the implementation of database write operations in the orchestrator module to persist pipeline execution data at appropriate stages.

## Implementation Summary

The orchestrator has been updated to call DB write APIs at the following pipeline stages:

### 1. Pipeline Start - Create Pipeline Run Entry
- **When**: At the beginning of pipeline execution
- **API Called**: `db_util.insert_pipeline_run(timestamp, alerts_count, raw_data_path)`
- **Data Stored**: 
  - Timestamp of pipeline start
  - Initial alerts_count (0, updated after Monitor stage)
  - Optional raw data path
- **Returns**: `run_id` used for all subsequent DB writes

### 2. After Monitor Stage - Update Alerts Count
- **When**: After MonitorAgent completes
- **Operation**: Updates the pipeline_runs record with actual alerts_count
- **Data Updated**: Number of alerts detected by MonitorAgent

### 3. After OpsLog Stage - Write Audit Summary
- **When**: After OpsLogAgent completes
- **API Called**: `db_util.insert_audit_summary(run_id, audit_dict)`
- **Data Stored**:
  - status: Audit status
  - count: Number of items audited
  - timestamp: Audit timestamp

### 4. After Governance Stage - Write Governance Analysis and Compliance Issues
- **When**: After LLMGovernanceAgent completes
- **APIs Called**:
  - `db_util.insert_governance_analysis(run_id, gov_dict)`
  - `db_util.insert_compliance_issues(run_id, issues_list)`
- **Data Stored**:
  - Governance Analysis:
    - risk: Risk level assessment
    - escalation: Escalation decision
    - commentary: Additional governance commentary
  - Compliance Issues: List of compliance issues detected

### 5. After Notification Stage - Write Notification Events
- **When**: After NotificationAgent completes
- **API Called**: `db_util.insert_notification_event(run_id, channel, status, response)`
- **Data Stored**: For each notification sent:
  - channel: Notification channel (e.g., "pushover", "gmail")
  - status: Notification status (e.g., "success", "failed")
  - response: Response from notification service

## Error Handling

The implementation follows the spec requirement that DB write failures should not abort pipeline execution:

1. **Graceful Degradation**: If `insert_pipeline_run` fails, the pipeline continues without DB persistence
2. **Error Logging**: All DB write failures are logged using the logger
3. **Status Tracking**: The `db_write_status` dictionary tracks success/failure of each DB write operation
4. **User Feedback**: Pipeline completion summary includes DB write status

## DB Write Status Tracking

The `PipelineExecutor` class now includes:

```python
self.run_id: Optional[int] = None
self.db_write_status = {
    'pipeline_run': False,
    'audit_summary': False,
    'governance_analysis': False,
    'compliance_issues': False,
    'notification_events': False
}
```

This status is included in the pipeline output for monitoring and debugging.

## Output Structure Changes

The pipeline now returns additional fields in the output:

```python
{
    'governance_output': {...},
    'notification_status': '...',
    'notifications_sent': [...],
    'db_write_status': {
        'pipeline_run': True/False,
        'audit_summary': True/False,
        'governance_analysis': True/False,
        'compliance_issues': True/False,
        'notification_events': True/False
    },
    'run_id': <integer>
}
```

## Testing

### Unit Tests Updated
- `tests/unit/test_orchestrator.py::test_pipeline_sequential_execution`
  - Updated to mock `db_util` module
  - Verifies all DB write APIs are called with correct parameters
  - Validates `db_write_status` and `run_id` in output

### Verification Script
- `scripts/verify_orchestrator_db_integration.py`
  - Checks database initialization
  - Verifies schema and tables
  - Confirms DB write APIs are available
  - Validates orchestrator imports and attributes
  - Checks for pipeline run data in database

## Compliance with Spec Requirements

✅ Create pipeline_runs entry at pipeline start or after OpsLog  
✅ Write audit_summary after OpsLog  
✅ Write governance_analysis and compliance issues after Governance step  
✅ Write notification_events after Notification step  
✅ DB write failures are logged and do not abort pipeline execution  
✅ DB write status is tracked and included in pipeline output  

## Next Steps

The orchestrator DB integration is complete. The next phase (Phase 5) will update the UI to read from the database instead of JSON files.
