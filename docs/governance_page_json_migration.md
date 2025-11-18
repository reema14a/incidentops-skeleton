# Governance Page JSON Migration

## Overview

This document describes the migration of the Governance page to use the `governance_data` JSON column instead of legacy columns (`risk`, `escalation`, `commentary`).

## Changes Made

### 1. Database Layer (`db/db_util.py`)

Updated `get_governance_history()` function to include the `governance_data` JSON column:

```python
# Added governance_data to SELECT query
SELECT 
    g.id,
    g.run_id,
    p.timestamp,
    g.risk,
    g.escalation,
    g.commentary,
    g.governance_data  # NEW
FROM governance_analysis g
```

The function now returns records with the `governance_data` field containing the full JSON string.

### 2. Governance Page (`ui/pages/Governance.py`)

#### Updated `get_latest_governance_data()` function:

- Parses `governance_data` JSON if available
- Falls back to legacy columns if JSON parsing fails or if `governance_data` is None
- Extracts all fields from JSON including:
  - `risk`
  - `escalation`
  - `commentary`
  - `compliance_issues` (list)
  - `risk_score` (if present)
  - `extra_metadata` (if present)
  - `additional_context` (if present)

#### Updated metadata display:

- Added **Pipeline Run ID** as the first column in the metadata row
- Changed from 3 columns to 4 columns to accommodate the new field

#### Updated compliance issues section:

- First attempts to get compliance issues from `governance_data` JSON
- Falls back to database query if not present in JSON
- This provides better performance and consistency

#### Updated collapsible details section:

- Displays the full `governance_data` JSON
- Shows additional fields if present:
  - `risk_score`
  - `extra_metadata`
  - `additional_context`

#### Updated historical governance records:

- Parses `governance_data` JSON for each historical record
- Falls back to legacy columns if JSON is not available
- Uses JSON data for compliance issues first, then falls back to database

## Backward Compatibility

The implementation maintains full backward compatibility:

1. **Legacy columns preserved**: The `risk`, `escalation`, and `commentary` columns are still queried and available
2. **Graceful fallback**: If `governance_data` is NULL or invalid JSON, the page falls back to legacy columns
3. **Existing tests pass**: All existing integration tests continue to pass without modification

## Benefits

1. **Single source of truth**: All governance data is stored in one JSON column
2. **Extensibility**: New fields can be added to the JSON without schema changes
3. **Consistency**: The JSON structure matches what the LLMGovernanceAgent produces
4. **Performance**: Fewer database queries needed (compliance issues included in JSON)
5. **Flexibility**: Supports additional fields like `risk_score`, `extra_metadata`, etc.

## Testing

Created new integration test: `tests/integration/test_governance_page_json_parsing.py`

Tests cover:
- Verification that `governance_data` field is returned by `get_governance_history()`
- JSON parsing and validation
- Expected fields presence in parsed JSON
- Legacy columns still available
- Fallback behavior when JSON is invalid or None

All tests pass successfully.

## Migration Path

For existing data:
1. Legacy columns (`risk`, `escalation`, `commentary`) continue to work
2. New pipeline runs will populate both legacy columns and `governance_data` JSON
3. The page automatically uses JSON when available, falls back to legacy columns otherwise
4. No data migration required

## Future Improvements

1. Consider deprecating legacy columns once all data has `governance_data` populated
2. Add more fields to the JSON structure as needed (e.g., `risk_score`, `recommendations`)
3. Consider adding a data migration script to backfill `governance_data` for old records
