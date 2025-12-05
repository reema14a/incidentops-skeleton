# Design Document

## Overview

The Tarot Oracle system integrates mystical symbolic guidance into the IncidentOps governance framework through two main components:

1. **MCP Tarot Server Tool** - A custom MCP tool (`tarot.draw`) that returns randomly selected tarot cards with meanings, risk alignments, and omen messages
2. **LLMGovernanceInsightsAgent
 Integration** - Extends the existing agent to invoke tarot readings and include them as "Shadow Risk Interpretations" in insights output
3. **Incident Intelligence UI Enhancement** - Adds a Tarot Interpretation panel to the existing Incident Intelligence page to display tarot readings alongside trend charts

The design follows existing IncidentOps patterns for MCP tools, agent architecture, and Streamlit UI components to ensure seamless integration with minimal code changes.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Tarot Oracle System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │  MCP Tarot Tool  │◄─────┤  LLMGovernanceInsightsAgent
 │    │
│  │  (tarot.draw)    │      │  (Enhanced)              │    │
│  └────────┬─────────┘      └──────────┬───────────────┘    │
│           │                            │                     │
│           │                            │                     │
│           ▼                            ▼                     │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │  MCP Router      │      │  Deep Governance         │    │
│  │  (Enhanced)      │      │  Insights Page           │    │
│  └──────────────────┘      │  (Enhanced with Tarot)   │    │
│                             └──────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Governance Integration Flow**:
   - LLMGovernanceInsightsAgent
 runs during pipeline execution
   - Agent invokes `tarot.draw` through MCP client
   - MCP router routes to tarot tool implementation
   - Tarot tool returns card data (name, meaning, risk_alignment, omen_message)
   - Tarot card data is included in insights output as "Shadow Risk Interpretation"
   - Card data is persisted to database with insights record
   - Incident Intelligence page displays tarot reading in dedicated panel alongside technical analysis

## Components and Interfaces

### 1. MCP Tarot Tool (`llm/local_mcp/tools/tarot_tool.py`)

**Purpose**: Implements the `tarot.draw` tool that returns randomly selected tarot cards.

**Interface**:
```python
def tarot_draw(arguments: Dict[str, Any], request_id: Optional[Any] = None) -> Dict[str, Any]:
    """Draw a random tarot card with meaning and risk interpretation.
    
    Args:
        arguments: Tool arguments (empty dict for random draw)
        request_id: Optional request ID for logging context
        
    Returns:
        dict: {
            "card_name": str,           # e.g., "The Tower"
            "meaning": str,             # Card interpretation
            "risk_alignment": str,      # e.g., "disruption", "stability"
            "omen_message": str         # Contextual message for incident ops
        }
    """
```

**Card Deck Structure**:
- Minimum 22 Major Arcana cards
- Each card has:
  - `name`: Card name (e.g., "The Fool", "The Tower")
  - `meaning`: Traditional tarot interpretation
  - `risk_alignment`: Governance concept mapping (stability, disruption, transformation, caution, opportunity)
  - `omen_message`: Contextual interpretation for incident operations

**Example Card Data**:
```python
{
    "name": "The Tower",
    "meaning": "Sudden change, upheaval, chaos, revelation, awakening",
    "risk_alignment": "disruption",
    "omen_message": "Beware of cascading failures. Systems built on unstable foundations may crumble. Prepare for unexpected incidents."
}
```

### 2. MCP Router Enhancement (`llm/local_mcp/router.py`)

**Changes Required**:
- Import `tarot_draw` from `llm.local_mcp.tools.tarot_tool`
- Add routing case for `'tarot.draw'` tool name
- Update supported tools list in error message

**Modified Routing Logic**:
```python
if tool_name == 'tarot.draw':
    return tarot_draw(arguments, request_id)
```

### 3. LLMGovernanceInsightsAgent
 Enhancement (`agents/llm_governance_insights_agent.py`)

**Changes Required**:
- Add MCP client import and initialization
- Invoke `tarot.draw` during insights generation
- Include tarot card data in insights output
- Handle MCP unavailability gracefully

**Enhanced `run()` Method Flow**:
1. Retrieve historical data (existing)
2. **NEW**: Invoke `tarot.draw` through MCP client
3. **NEW**: Add tarot card to insights context
4. Generate LLM insights (existing)
5. **NEW**: Include tarot card in output as "shadow_risk_interpretation"
6. Return insights with tarot data

**Output Schema Enhancement**:
```python
{
    'governance_output': {...},  # Existing
    'insights': {
        'trend_summary': str,
        'risk_trend': str,
        # ... existing fields ...
        'shadow_risk_interpretation': {  # NEW
            'card_name': str,
            'meaning': str,
            'risk_alignment': str,
            'omen_message': str
        }
    }
}
```

**Error Handling**:
- If MCP client fails, log warning and continue without tarot data
- Set `shadow_risk_interpretation` to `None` on failure
- Ensure agent never fails due to tarot integration

### 4. Incident Intelligence Page Enhancement (`ui/pages/Deep_Governance_Insights.py`)

**Purpose**: Display tarot interpretations alongside existing governance insights and trend charts.

**Layout Addition**:
```
┌─────────────────────────────────────────┐
│  [Existing Insights Display]            │
│  [Existing Trend Charts]                │
├─────────────────────────────────────────┤
│  🔮 Tarot Interpretation                │
│  ┌────────────────────────────────────┐ │
│  │  Card Name (Large, Mystical)       │ │
│  │  Meaning                            │ │
│  │  Risk Alignment Badge               │ │
│  │  Omen Message (Emphasized)         │ │
│  └────────────────────────────────────┘ │
│                                          │
└─────────────────────────────────────────┘
```

**Styling Theme**:
- Mystical accent colors (purple: #9d4edd, gold: #ffd700)
- Atmospheric typography for tarot section
- Subtle styling to distinguish from technical insights
- Emoji integration (🔮, 🌙, ⭐)

**Display Logic**:
1. Check if insights data includes `shadow_risk_interpretation`
2. If present, display Tarot Interpretation panel
3. Show card name, meaning, risk alignment badge, and omen message
4. If not present, display: "No tarot reading available for this insight"
5. Maintain existing page layout and functionality

**Error Handling**:
- Gracefully handle None or missing tarot data
- Display fallback message without disrupting page
- No errors if tarot data is unavailable

### 5. Database Schema Enhancement

**New Column in `insights_history` Table**:
```sql
ALTER TABLE insights_history 
ADD COLUMN tarot_card TEXT;  -- JSON string containing card data
```

**Card Data Storage Format**:
```json
{
    "card_name": "The Tower",
    "meaning": "Sudden change, upheaval...",
    "risk_alignment": "disruption",
    "omen_message": "Beware of cascading failures..."
}
```

## Data Models

### Tarot Card Model

```python
{
    "card_name": str,           # Card name (e.g., "The Fool")
    "meaning": str,             # Traditional interpretation
    "risk_alignment": str,      # One of: stability, disruption, transformation, caution, opportunity
    "omen_message": str         # Contextual message for incident operations
}
```

### Enhanced Insights Model

```python
{
    "governance_output": dict,  # Existing governance data
    "insights": {
        "trend_summary": str,
        "risk_trend": str,
        "compliance_trend": str,
        "recurring_issues": list,
        "category_hotspots": list,
        "recommendations": list,
        "anomaly_detection": str,
        "shadow_risk_interpretation": {  # NEW
            "card_name": str,
            "meaning": str,
            "risk_alignment": str,
            "omen_message": str
        } | None
    }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Card structure completeness
*For any* invocation of tarot.draw, the returned dictionary should contain all required fields (card_name, meaning, risk_alignment, omen_message) with non-empty string values
**Validates: Requirements 1.1**

### Property 2: Valid risk alignment values
*For any* card in the tarot deck, the risk_alignment field should be one of the allowed governance concepts (stability, disruption, transformation, caution, opportunity)
**Validates: Requirements 1.3**

### Property 3: Omen message presence
*For any* card in the tarot deck, the omen_message field should exist and contain a non-empty string
**Validates: Requirements 1.4**

### Property 4: Shadow risk interpretation inclusion
*For any* successful tarot draw during insights generation, the output should include a shadow_risk_interpretation field with complete card data
**Validates: Requirements 2.2**

### Property 5: Tarot data persistence round trip
*For any* insights record with tarot card data, storing to the database and then retrieving should return equivalent tarot card information
**Validates: Requirements 2.4**

## Error Handling

### MCP Tarot Tool Error Handling

**Scenarios**:
1. **Empty arguments**: Accept empty dict, return random card
2. **Invalid request_id**: Log with "None" or provided value, continue execution
3. **Random selection failure**: Should never occur with proper deck initialization, but log error if it does

**Error Response Format**:
```python
{
    "error": str,           # Error description
    "card_name": None,
    "meaning": None,
    "risk_alignment": None,
    "omen_message": None
}
```

### LLMGovernanceInsightsAgent
 Error Handling

**Scenarios**:
1. **MCP client unavailable**: Log warning, set `shadow_risk_interpretation` to `None`, continue with insights generation
2. **MCP call timeout**: Log warning, set `shadow_risk_interpretation` to `None`, continue
3. **Invalid tarot response**: Log warning, set `shadow_risk_interpretation` to `None`, continue
4. **Database storage failure**: Log error, but don't fail insights generation

**Graceful Degradation**:
- Agent must never fail due to tarot integration
- All existing functionality must work even if tarot is unavailable
- Warnings logged but not raised as exceptions

### Incident Intelligence Page Error Handling

**Scenarios**:
1. **No tarot data available**: Display message: "No tarot reading available for this insight"
2. **Invalid card data structure**: Display fallback message without breaking page
3. **Missing fields in tarot data**: Display available fields only

**Error Display Styling**:
- Maintain mystical theme for tarot section
- Use subtle styling for "not available" messages
- Include mystical emoji (🌙, 🔮)

## Testing Strategy

### Unit Testing

**MCP Tarot Tool Tests** (`tests/local_mcp_server/test_tarot_tool.py`):
- Test card deck has at least 22 cards
- Test all cards have required fields
- Test random selection returns valid card
- Test request_id logging
- Test error handling for edge cases

**LLMGovernanceInsightsAgent
 Tests** (`tests/unit/test_governance_insights.py` - enhanced):
- Mock MCP client to return tarot card data
- Verify shadow_risk_interpretation included in output
- Test graceful degradation when MCP fails
- Verify existing functionality unchanged

**Router Tests** (`tests/local_mcp_server/test_router.py` - enhanced):
- Test routing of `tarot.draw` to tarot tool
- Verify tool registration
- Test error handling for unknown tools

### Integration Testing

**MCP Client to Tarot Server** (`tests/e2e/test_mcp_tarot_integration.py`):
- Test end-to-end tarot.draw invocation through MCP client
- Verify JSON-RPC 2.0 compliance
- Test error scenarios (server down, timeout)

**LLMGovernanceInsightsAgent
 with Tarot** (`tests/integration/test_governance_insights_tarot.py`):
- Test full insights generation with tarot integration
- Verify database persistence of tarot data
- Test retrieval of insights with tarot from database

**Streamlit UI Tests** (`tests/integration/test_deep_governance_insights_tarot.py`):
- Test tarot panel renders when data present
- Test card display with valid data
- Test graceful handling when tarot data is None
- Test page layout remains intact with tarot panel

### Property-Based Testing

**Property Tests** (`tests/unit/test_tarot_properties.py`):
- Property 1: Card structure completeness (100 iterations)
- Property 2: Valid risk alignment values (all cards in deck)
- Property 3: Omen message presence (all cards in deck)
- Property 4: Shadow risk interpretation inclusion (100 iterations with mocked MCP)
- Property 5: Tarot data persistence round trip (100 iterations)

**Testing Framework**: Use `pytest` with `hypothesis` for property-based testing

**Configuration**:
- Minimum 100 iterations per property test
- Each property test tagged with comment referencing design document
- Tag format: `# Feature: tarot-oracle, Property {number}: {property_text}`

## Implementation Notes

### Tarot Card Deck Design

**Major Arcana Cards** (22 minimum):
1. The Fool - new beginnings, innocence - opportunity
2. The Magician - manifestation, resourcefulness - opportunity
3. The High Priestess - intuition, sacred knowledge - caution
4. The Empress - abundance, nurturing - stability
5. The Emperor - authority, structure - stability
6. The Hierophant - tradition, conformity - stability
7. The Lovers - harmony, relationships - opportunity
8. The Chariot - control, willpower - transformation
9. Strength - courage, patience - stability
10. The Hermit - introspection, solitude - caution
11. Wheel of Fortune - cycles, destiny - transformation
12. Justice - fairness, truth - stability
13. The Hanged Man - suspension, letting go - caution
14. Death - endings, transformation - transformation
15. Temperance - balance, moderation - stability
16. The Devil - bondage, materialism - caution
17. The Tower - upheaval, chaos - disruption
18. The Star - hope, inspiration - opportunity
19. The Moon - illusion, intuition - caution
20. The Sun - success, vitality - opportunity
21. Judgement - reflection, reckoning - transformation
22. The World - completion, accomplishment - opportunity

### Tarot Card Image Filename Convention

Tarot card images are stored in `ui/assets/` and must follow a filename
derived from the `card_name` returned by the `tarot.draw` tool.

Filename derivation:

- Convert the card name to lowercase.
- Replace spaces with underscores.
- Resolve the file using `.png` or `.jpeg`.
- Use the first matching file found.
- Missing images must be handled gracefully by the UI.

Example:
"The Tower" → `ui/assets/the_tower.png` or `ui/assets/the_tower.jpeg`

### Styling Constants

**Color Palette**:
```python
COLORS = {
    'background_dark': '#1a1a2e',
    'background_medium': '#16213e',
    'accent_purple': '#9d4edd',
    'accent_gold': '#ffd700',
    'text_light': '#e0e0e0',
    'error_red': '#8b0000'
}
```

**Risk Alignment Colors**:
```python
RISK_COLORS = {
    'stability': '#4caf50',      # Green
    'disruption': '#f44336',     # Red
    'transformation': '#9c27b0', # Purple
    'caution': '#ff9800',        # Orange
    'opportunity': '#2196f3'     # Blue
}
```

### Database Migration

**Migration Script** (if needed):
```sql
-- Add tarot_card column to insights_history table
ALTER TABLE insights_history 
ADD COLUMN tarot_card TEXT DEFAULT NULL;
```

**Note**: Column should accept NULL values for backward compatibility with existing records.

## Dependencies

**No new external dependencies required**. The feature uses:
- Existing `llm.mcp_client` for MCP communication
- Existing `db.db_util` for database operations
- Existing `streamlit` for UI
- Python standard library `random` for card selection
- Python standard library `json` for data serialization

## Performance Considerations

**Tarot Tool Performance**:
- Card selection is O(1) using random.choice()
- No external API calls
- Response time < 1ms for local execution

**Agent Performance Impact**:
- Single MCP call adds ~10-50ms to insights generation
- Negligible impact on overall pipeline execution time
- Async/await not required due to fast response time

**UI Performance**:
- Card display is instant once data received
- No heavy rendering or animations
- Page load time unaffected

## Security Considerations

**No security concerns**:
- No external API calls
- No user input validation required (empty arguments)
- No sensitive data in tarot cards
- No authentication/authorization needed
- Read-only operation (no data modification)

## Backward Compatibility

**Guaranteed Compatibility**:
- Existing agents unchanged (except LLMGovernanceInsightsAgent
 enhancement)
- Existing MCP tools continue working
- Existing database schema compatible (new column is nullable)
- Existing UI pages unaffected
- Existing tests continue passing

**Migration Path**:
- Deploy MCP tarot tool first
- Update router to register new tool
- Enhance LLMGovernanceInsightsAgent
 with optional tarot integration
- Add database column (nullable)
- Deploy Tarot Oracle UI page
- No downtime required
