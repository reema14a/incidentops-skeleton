# Tarot Oracle Output Schema

## Overview

The Tarot Oracle system provides mystical guidance through tarot card readings integrated into the IncidentOps governance framework. This document defines the output schema for the `tarot.draw` MCP tool.

## Tarot Card Schema

### Tool: `tarot.draw`

**Location**: `llm/local_mcp/tools/tarot_tool.py`

**Function**: `tarot_draw(arguments: Dict[str, Any], request_id: Optional[Any] = None) -> Dict[str, Any]`

### Output Schema

```python
{
    "card_name": str,           # Card name (e.g., "The Tower", "The Fool")
    "meaning": str,             # Traditional tarot interpretation
    "risk_alignment": str,      # Governance concept mapping
    "omen_message": str         # Contextual message for incident operations
}
```

### Field Descriptions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `card_name` | string | Yes | Name of the tarot card drawn | "The Tower" |
| `meaning` | string | Yes | Traditional tarot card interpretation | "Sudden change, upheaval, chaos, revelation, awakening" |
| `risk_alignment` | string | Yes | Governance concept mapping | "disruption" |
| `omen_message` | string | Yes | Contextual interpretation for incident operations | "Beware of cascading failures. Systems built on unstable foundations may crumble." |

### Risk Alignment Values

The `risk_alignment` field maps tarot cards to governance concepts. Valid values:

- **`stability`** - Systems are stable, maintain current practices
- **`disruption`** - Potential for sudden changes or failures
- **`transformation`** - Change is necessary or underway
- **`caution`** - Proceed carefully, hidden risks may exist
- **`opportunity`** - Favorable conditions for improvement

### Example Output

```json
{
    "card_name": "The Tower",
    "meaning": "Sudden change, upheaval, chaos, revelation, awakening",
    "risk_alignment": "disruption",
    "omen_message": "Beware of cascading failures. Systems built on unstable foundations may crumble. Prepare for unexpected incidents."
}
```

### Error Handling

If the tarot tool encounters an error, it raises an exception:

```python
raise Exception(f"Failed to draw tarot card: {error_message}")
```

The calling agent (GovernanceInsightsAgent) is responsible for handling this exception gracefully.

## Integration Points

### 1. GovernanceInsightsAgent

**Status**: ⚠️ NOT YET IMPLEMENTED

The GovernanceInsightsAgent should invoke the tarot tool and include the card data in its output:

```python
# Expected integration (not yet implemented)
insights_output = {
    'governance_output': {...},
    'insights': {
        'trend_summary': str,
        'risk_trend': str,
        'compliance_trend': str,
        'recurring_issues': list,
        'category_hotspots': list,
        'recommendations': list,
        'anomaly_detection': str,
        'shadow_risk_interpretation': {  # NEW - not yet implemented
            'card_name': str,
            'meaning': str,
            'risk_alignment': str,
            'omen_message': str
        } | None
    }
}
```

### 2. Database Storage

**Status**: ⚠️ NOT YET IMPLEMENTED

The `insights_history` table should store tarot card data:

```sql
-- Expected schema (not yet implemented)
ALTER TABLE insights_history 
ADD COLUMN tarot_card TEXT;  -- JSON string containing card data
```

### 3. Deep Governance Insights UI

**Status**: ⚠️ NOT YET IMPLEMENTED

The UI should display tarot interpretations when available:

```python
# Expected UI logic (not yet implemented)
if insights.get('shadow_risk_interpretation'):
    display_tarot_panel(insights['shadow_risk_interpretation'])
else:
    display_message("No tarot reading available for this insight")
```

## Validation

### Property Tests

The following properties should be validated:

1. **Card structure completeness**: All returned cards must have all 4 required fields with non-empty string values
2. **Valid risk alignment values**: `risk_alignment` must be one of: stability, disruption, transformation, caution, opportunity
3. **Omen message presence**: `omen_message` must exist and be non-empty

### Unit Tests

Location: `tests/local_mcp_server/test_tarot_tool.py`

Required tests:
- Test deck has at least 22 cards
- Test all cards have required fields
- Test random selection returns valid card
- Test request_id logging
- Test error handling for edge cases

## Schema Version

**Version**: 1.0.0  
**Last Updated**: 2025-11-21  
**Status**: Implemented (integration pending)

## Related Documentation

- [Tarot Oracle Requirements](.kiro/specs/tarot-oracle/requirements.md)
- [Tarot Oracle Design](.kiro/specs/tarot-oracle/design.md)
- [Tarot Oracle Tasks](.kiro/specs/tarot-oracle/tasks.md)
- [Insights Schema](docs/insights_schema.md)
- [Pipeline Flow](docs/pipeline_flow.md)
