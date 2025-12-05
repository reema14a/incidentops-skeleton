# LLMGovernanceInsightsAgent
 Implementation

## Overview

The LLMGovernanceInsightsAgent
 is a new LLM-based agent that analyzes historical governance data to provide trend analysis, recurring issue detection, and actionable recommendations for engineering leadership.

## Implementation Details

### Agent Location
- **File**: `agents/llm_governance_insights_agent.py`
- **Class**: `LLMGovernanceInsightsAgent
`
- **Base Class**: `BaseAgent`

### Pipeline Position
The agent is positioned as Stage 7 in the pipeline, between LLMGovernanceAgent and NotificationAgent:

1. MonitorAgent
2. LLMAlertSummaryAgent
3. TriageAgent
4. LLMResolutionAgent
5. OpsLogAgent
6. LLMGovernanceAgent
7. **LLMGovernanceInsightsAgent
** ← NEW
8. NotificationAgent

### Key Features

#### 1. Historical Data Retrieval
The agent retrieves aggregated historical data using DB utility functions:
- `get_risk_trend()` - Risk levels over time
- `get_compliance_trend()` - Compliance issue counts over time
- `get_escalation_text_counts()` - Escalation frequency analysis
- `get_recent_runs(limit=10)` - Recent pipeline run metadata
- `get_category_distribution()` - Category frequency across runs
- `get_severity_distribution()` - Severity frequency across runs

#### 2. LLM Analysis
The agent uses the `governance_insights_prompt` from `config/prompts.yaml` to analyze historical data and generate:
- **trend_summary**: High-level description of patterns
- **risk_trend**: Observations about risk level changes
- **compliance_trend**: How compliance issues have evolved
- **recurring_issues**: List of recurring themes
- **category_hotspots**: Frequently occurring categories/severities
- **recommendations**: Actionable recommendations for leadership
- **anomaly_detection**: Abnormalities or outliers

#### 3. Fallback Behavior
When LLM analysis fails or insufficient data exists, the agent provides:
- Basic statistical analysis from DB data
- Helpful messages about data availability
- Recommendations to continue running the pipeline

### Database Integration

#### New Table: insights_history
Created by migration v4 in `db/db_util.py`:
```sql
CREATE TABLE insights_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    insights_data TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
)
```

#### New DB Functions
- `insert_insights_history(run_id, insights_json)` - Store insights for a run
- `get_insights_history(limit)` - Retrieve historical insights

### Orchestrator Changes

#### Modified Files
- `orchestrator/orchestrator.py`

#### Changes Made
1. Added `LLMGovernanceInsightsAgent
` import
2. Added agent to `self.agents` dictionary
3. Added `insights_history` to `db_write_status` tracking
4. Added `_validate_insights_output()` validation method
5. Added Stage 7 execution step
6. Added DB write for insights_history
7. Updated pipeline output to include insights
8. Updated pipeline summary display

### Testing

#### Unit Tests
**File**: `tests/unit/test_governance_insights.py`

Tests:
- `test_llm_governance_insights_agent()` - Normal operation with mock data
- `test_governance_insights_no_data()` - Handles insufficient historical data
- `test_governance_insights_fallback()` - Handles LLM failure gracefully

#### Integration Tests
**File**: `tests/integration/test_governance_insights_integration.py`

Tests:
- `test_pipeline_with_governance_insights()` - Full pipeline integration

#### E2E Tests
**File**: `tests/e2e/test_full_roundtrip.py`

Updated to verify:
- Insights field exists in pipeline output
- All required insights fields are present
- Field types are correct

### Configuration

#### Prompt Template
Added to `config/prompts.yaml`:
```yaml
governance_insights_prompt: |
  You are an AI assistant responsible for analyzing historical incident governance data.
  You will be given structured JSON representing multiple past pipeline runs,
  including governance analysis, compliance findings, category distributions,
  severity distributions, and escalation patterns.
  
  Your task is to produce a JSON object with the following fields:
    - trend_summary: high-level description of notable patterns across runs
    - risk_trend: observations about changes in risk levels over time
    - compliance_trend: how compliance issues have evolved
    - recurring_issues: list of recurring risk themes or compliance problems
    - category_hotspots: categories or severities that appear frequently
    - recommendations: short, actionable recommendations for engineering leadership
    - anomaly_detection: any abnormalities or outliers in the data
  
  Your output must be strictly valid JSON with these keys.
```

## Usage

The agent runs automatically as part of the pipeline. No manual invocation is required.

### Pipeline Execution
```bash
python3 -m ui.console_client
```

### Accessing Insights
Insights are available in:
1. Pipeline output: `result['insights']`
2. Database: `get_insights_history()` function
3. Console output during pipeline execution

## Benefits

1. **Trend Analysis**: Identifies patterns in incident frequency, severity, and risk levels
2. **Proactive Recommendations**: Provides actionable guidance for engineering teams
3. **Historical Context**: Helps understand how system health evolves over time
4. **Anomaly Detection**: Highlights unusual patterns that may require investigation
5. **Compliance Tracking**: Monitors compliance issue trends for regulatory purposes

## Future Enhancements

Potential improvements:
- Add time-series forecasting for incident prediction
- Implement automated alerting for negative trends
- Add comparative analysis across different time periods
- Integrate with external monitoring systems
- Add custom insight templates for different stakeholders
