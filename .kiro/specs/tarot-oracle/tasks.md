# Implementation Plan

- [x] 1. Implement MCP Tarot Tool
  - Create `llm/local_mcp/tools/tarot_tool.py` with `tarot_draw()` function
  - Define tarot card deck with 22 Major Arcana cards
  - Each card must include: name, meaning, risk_alignment, omen_message
  - Implement random card selection using Python's random.choice()
  - Add logging with request_id context
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.1 Write property test for card structure completeness
  - **Property 1: Card structure completeness**
  - **Validates: Requirements 1.1**

- [ ]* 1.2 Write property test for valid risk alignment values
  - **Property 2: Valid risk alignment values**
  - **Validates: Requirements 1.3**

- [ ]* 1.3 Write property test for omen message presence
  - **Property 3: Omen message presence**
  - **Validates: Requirements 1.4**

- [ ]* 1.4 Write unit tests for tarot tool
  - Test deck has at least 22 cards
  - Test random selection returns valid card
  - Test request_id logging
  - Create `tests/local_mcp_server/test_tarot_tool.py`
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Update MCP Router
  - Modify `llm/local_mcp/router.py` to import tarot_tool
  - Add routing case for 'tarot.draw' tool name
  - Update error message with new supported tool
  - _Requirements: 1.5, 4.3_

- [ ]* 2.1 Write unit tests for router enhancement
  - Test routing of tarot.draw to tarot tool
  - Verify tool registration
  - Update `tests/local_mcp_server/test_router.py`
  - _Requirements: 1.5, 4.3_

- [x] 3. Enhance GovernanceInsightsAgent
  - Import and initialize MCP client in `agents/llm_governance_insights_agent.py`
  - Add `_draw_tarot_card()` method to invoke tarot.draw through MCP
  - Modify `run()` method to call `_draw_tarot_card()` before LLM insights generation
  - Include tarot card data in insights output as 'shadow_risk_interpretation'
  - Implement graceful error handling (log warning, set to None on failure)
  - Ensure agent never fails due to tarot integration
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [ ]* 3.1 Write property test for shadow risk interpretation inclusion
  - **Property 4: Shadow risk interpretation inclusion**
  - **Validates: Requirements 2.2**

- [ ]* 3.2 Write unit tests for agent enhancement
  - Mock MCP client to return tarot card data
  - Verify shadow_risk_interpretation included in output
  - Test graceful degradation when MCP fails
  - Verify existing functionality unchanged
  - Update `tests/unit/test_governance_insights.py`
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 4. Add database support for tarot data
  - Add `tarot_card` TEXT column to `insights_history` table in `db/db_util.py`
  - Column should be nullable for backward compatibility
  - Update `insert_insights_history()` to accept and store tarot_card JSON
  - Update `get_insights_history()` to retrieve tarot_card data
  - _Requirements: 2.4_

- [ ]* 4.1 Write property test for tarot data persistence
  - **Property 5: Tarot data persistence round trip**
  - **Validates: Requirements 2.4**

- [ ]* 4.2 Write unit tests for database operations
  - Test inserting insights with tarot card data
  - Test retrieving insights with tarot card data
  - Test NULL handling for backward compatibility
  - Update `tests/unit/test_insert_insights_history.py` and `tests/unit/test_get_insights_history.py`
  - _Requirements: 2.4_

- [x] 5. Update Deep Governance Insights page
  - Modify `ui/pages/Deep_Governance_Insights.py` to display tarot card data
  - Add "🔮 Tarot Interpretation" panel after existing insights sections
  - Show card name, meaning, risk alignment badge, and omen message
  - Apply mystical styling to tarot panel (colors: #9d4edd, #ffd700)
  - Handle None case gracefully (display "No tarot reading available")
  - Ensure existing page layout and functionality remain intact
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 5.1 Write integration tests for Deep Governance Insights enhancement
  - Test tarot panel displays when data present
  - Test card display with valid data
  - Test graceful handling when tarot data is None
  - Test page layout remains intact with tarot panel
  - Update `tests/integration/test_deep_governance_insights_tarot.py`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. End-to-end integration testing
  - Test full MCP client to tarot server flow
  - Test GovernanceInsightsAgent with tarot integration
  - Test database persistence and retrieval
  - Test UI displays tarot data correctly in Deep Governance Insights page
  - Verify backward compatibility with existing tests
  - Create `tests/e2e/test_tarot_oracle_e2e.py`
  - _Requirements: 4.2, 4.5_
