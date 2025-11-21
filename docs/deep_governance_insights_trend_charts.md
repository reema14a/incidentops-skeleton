# Deep Governance Insights - DB-Backed Trend Charts Implementation

## Overview

This document describes the implementation of optional DB-backed trend charts for the Deep Governance Insights page.

## Implementation Date

November 20, 2025

## Changes Made

### 1. Added Helper Functions

Added three new helper functions to `ui/pages/Deep_Governance_Insights.py`:

- `get_risk_trend()` - Retrieves risk trend data from database
- `get_compliance_trend()` - Retrieves compliance trend data from database
- `get_escalation_text_counts()` - Retrieves escalation frequency data from database
- `get_risk_emoji(risk_level)` - Returns appropriate emoji for risk level display

### 2. Added Historical Trend Charts Section

Added a new section titled "📊 Historical Trend Charts" with three tabs:

#### Tab 1: Risk Trend
- Line chart showing risk levels over time
- Maps risk levels to numeric values (1=Low, 2=Medium, 3=High, 4=Critical)
- Displays detailed breakdown in expandable section
- Shows most recent 10 records with emojis

#### Tab 2: Compliance Trend
- Line chart showing compliance issue counts over time
- Displays detailed breakdown in expandable section
- Shows most recent 10 records with success/warning icons

#### Tab 3: Escalation Frequency
- Bar chart showing frequency of different escalation recommendations
- Displays detailed breakdown in expandable section
- Sorted by frequency (most common first)

### 3. Graceful Handling of Empty Data

All trend charts display informative messages when no data is available:
- "No risk trend data available. Run the pipeline multiple times to generate trend data."
- "No compliance trend data available. Run the pipeline multiple times to generate trend data."
- "No escalation data available. Run the pipeline multiple times to generate trend data."

## Database Functions Used

The implementation leverages existing database utility functions from `db/db_util.py`:

- `db_util.get_risk_trend()` - Returns list of risk trend records
- `db_util.get_compliance_trend()` - Returns list of compliance trend records
- `db_util.get_escalation_text_counts()` - Returns dict of escalation text counts

## Testing

Created comprehensive integration tests in `tests/integration/test_deep_governance_insights_trend_charts.py`:

- `test_get_risk_trend()` - Verifies function returns a list
- `test_get_compliance_trend()` - Verifies function returns a list
- `test_get_escalation_text_counts()` - Verifies function returns a dict
- `test_get_risk_emoji()` - Verifies correct emojis for all risk levels
- `test_risk_trend_data_structure()` - Validates data structure when data exists
- `test_compliance_trend_data_structure()` - Validates data structure when data exists
- `test_escalation_counts_data_structure()` - Validates data structure when data exists

All tests pass successfully.

## User Experience

### Before
- Deep Governance Insights page showed only the latest insights from GovernanceInsightsAgent
- No historical trend visualization available

### After
- Deep Governance Insights page now includes historical trend charts
- Users can visualize risk trends, compliance trends, and escalation frequency across all pipeline runs
- Charts are optional and gracefully handle cases with no data
- Detailed breakdowns available in expandable sections

## Technical Details

### Data Flow
1. User navigates to Deep Governance Insights page
2. Page retrieves latest insights from `insights_history` table
3. Page also retrieves historical trend data from database:
   - Risk levels from `governance_analysis` table
   - Compliance issue counts from `compliance_issues` table
   - Escalation recommendations from `governance_analysis` table
4. Data is formatted and displayed in interactive charts

### Chart Types
- **Line Charts**: Used for risk and compliance trends (time-series data)
- **Bar Charts**: Used for escalation frequency (categorical data)

### Styling
- Consistent with existing Governance page styling
- Uses Streamlit's native chart components
- Includes emojis for visual clarity (🟢🟡🟠🔴)
- Expandable sections for detailed data

## Future Enhancements

Potential improvements for future iterations:

1. Add date range filtering for trend charts
2. Add export functionality for trend data
3. Add comparison views (e.g., compare two time periods)
4. Add statistical analysis (e.g., trend direction, rate of change)
5. Add interactive tooltips with more details

## Related Files

- `ui/pages/Deep_Governance_Insights.py` - Main implementation
- `db/db_util.py` - Database utility functions
- `tests/integration/test_deep_governance_insights_trend_charts.py` - Integration tests
- `.kiro/specs/streamlit_ui.spec.md` - Specification document

## Conclusion

The DB-backed trend charts feature has been successfully implemented for the Deep Governance Insights page. The implementation follows the existing patterns from the Governance page, provides graceful handling of empty data, and includes comprehensive testing.
