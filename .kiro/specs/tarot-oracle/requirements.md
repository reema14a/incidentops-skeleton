# Requirements Document

## Introduction

The Tarot Oracle system integrates mystical guidance into the IncidentOps governance framework. By exposing tarot card readings through a custom MCP server, the system provides "Shadow Risk Interpretations" that complement traditional governance insights with symbolic wisdom. The feature integrates directly into the existing Deep Governance Insights page, adding a Tarot Interpretation panel alongside existing trend charts and analysis.

## Glossary

- **Tarot Oracle System**: The complete feature including MCP server, agent integration, and UI components
- **MCP Tarot Server**: A custom Model Context Protocol server that exposes tarot card drawing functionality
- **Shadow Risk Interpretation**: A tarot-based symbolic interpretation included in governance insights
- **GovernanceInsightsAgent**: The existing LLM agent responsible for generating governance analysis
- **Tarot Card**: A symbolic card with associated meanings, risk alignments, and omen messages
- **Tarot Interpretation Panel**: A UI component on the Deep Governance Insights page displaying tarot readings

## Requirements

### Requirement 1

**User Story:** As a system operator, I want to draw tarot cards through an MCP server, so that I can receive symbolic guidance about system risks.

#### Acceptance Criteria

1. WHEN the MCP Tarot Server receives a tarot.draw request THEN the system SHALL return a randomly selected tarot card with its name, meaning, risk alignment, and omen message
2. WHEN the tarot.draw tool is invoked THEN the system SHALL select from a complete deck of at least 22 Major Arcana cards
3. WHEN a card is drawn THEN the system SHALL include a risk_alignment field mapping the card to governance concepts (e.g., "stability", "disruption", "transformation")
4. WHEN a card is drawn THEN the system SHALL include an omen_message field providing contextual interpretation for incident operations
5. WHEN the MCP Tarot Server starts THEN the system SHALL register the tarot.draw tool with proper JSON-RPC 2.0 compliance

### Requirement 2

**User Story:** As a governance analyst, I want tarot readings integrated into governance insights, so that I can see symbolic interpretations alongside technical analysis.

#### Acceptance Criteria

1. WHEN the GovernanceInsightsAgent generates insights THEN the system SHALL invoke the tarot.draw tool through the MCP client
2. WHEN a tarot card is drawn during insights generation THEN the system SHALL include it as a "Shadow Risk Interpretation" section in the output
3. WHEN the MCP Tarot Server is unavailable THEN the GovernanceInsightsAgent SHALL continue functioning and log a warning without failing
4. WHEN storing insights to the database THEN the system SHALL persist the tarot card data (name, meaning, risk_alignment, omen_message) in the insights record
5. WHEN the tarot integration fails THEN the system SHALL gracefully degrade and provide insights without the tarot component

### Requirement 3

**User Story:** As a user, I want to see tarot interpretations on the Deep Governance Insights page, so that I can view symbolic guidance alongside technical analysis.

#### Acceptance Criteria

1. WHEN a user views the Deep Governance Insights page THEN the system SHALL display a "Tarot Interpretation" panel with mystical styling
2. WHEN insights include tarot card data THEN the system SHALL display the card name, meaning, risk alignment, and omen message in the panel
3. WHEN displaying a tarot card THEN the system SHALL use atmospheric visual styling including mystical colors and appropriate typography
4. WHEN no tarot data is available THEN the system SHALL display a message indicating "No tarot reading available for this insight"
5. WHEN the tarot panel is displayed THEN the system SHALL maintain the existing page layout without disrupting trend charts or other insights

### Requirement 4

**User Story:** As a developer, I want the Tarot Oracle system to follow existing MCP patterns, so that it integrates seamlessly with the current architecture.

#### Acceptance Criteria

1. WHEN implementing the MCP Tarot Server THEN the system SHALL follow the same structure as existing local MCP tools (gmail_tool.py, pushover_tool.py)
2. WHEN the Tarot Oracle system is deployed THEN the system SHALL require no changes to existing orchestrator or pipeline logic
3. WHEN the MCP Tarot Server is added THEN the system SHALL register its tools through the existing router.py mechanism
4. WHEN implementing the feature THEN the system SHALL use the existing mcp_client.py for all MCP communication
5. WHEN the feature is complete THEN the system SHALL maintain backward compatibility with all existing agents and workflows

### Requirement 5

**User Story:** As a system administrator, I want the Tarot Oracle feature to be lightweight, so that it doesn't impact system performance or complexity.

#### Acceptance Criteria

1. WHEN the Tarot Oracle system is implemented THEN the system SHALL add no more than 2 new Python files (tarot_tool.py and minimal UI changes)
2. WHEN the MCP Tarot Server runs THEN the system SHALL use minimal memory and CPU resources
3. WHEN tarot cards are drawn THEN the system SHALL respond within 100 milliseconds
4. WHEN the feature is deployed THEN the system SHALL require no additional external dependencies beyond existing requirements
5. WHEN the Tarot Interpretation panel renders THEN the system SHALL not impact page load time by more than 100 milliseconds
