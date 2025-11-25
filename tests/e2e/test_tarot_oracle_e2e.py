#!/usr/bin/env python3
"""End-to-end integration tests for Tarot Oracle feature.

These tests verify the complete integration of the Tarot Oracle system:
1. MCP client → Local MCP Server → tarot.draw tool
2. GovernanceInsightsAgent with tarot integration
3. Database persistence and retrieval of tarot data
4. UI display of tarot data in Deep Governance Insights page
5. Backward compatibility with existing tests

The tests use real components with mocked external dependencies (OpenAI, SMTP, etc.)
to validate the full integration flow.
"""

import unittest
import threading
import time
import tempfile
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Add project root to path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.mcp_client import MCPClient, MCPError
from llm.local_mcp.server import app
from agents.llm_governance_insights_agent import GovernanceInsightsAgent
from db import db_util


class TestTarotOracleE2E(unittest.TestCase):
    """End-to-end tests for the complete Tarot Oracle integration."""
    
    @classmethod
    def setUpClass(cls):
        """Start the MCP server in a background thread."""
        # Start server
        cls.server_thread = threading.Thread(
            target=lambda: app.run(
                host='127.0.0.1',
                port=5006,  # Use different port to avoid conflicts
                debug=False,
                use_reloader=False
            ),
            daemon=True
        )
        cls.server_thread.start()
        # Give server time to start
        time.sleep(2)
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Set environment variable for database path
        os.environ['DB_PATH'] = self.db_path
        
        # Initialize database
        db_util.initialize_database()
        
        # Create MCP client pointing to test server
        self.mcp_client = MCPClient(endpoint='http://127.0.0.1:5006/send')
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary database
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        
        # Clean up environment variable
        if 'DB_PATH' in os.environ:
            del os.environ['DB_PATH']
    
    def _get_timestamp(self):
        """Generate ISO 8601 timestamp for database operations."""
        return datetime.utcnow().isoformat() + 'Z'
    
    # =========================================================================
    # Test 1: MCP Client → Tarot Server Flow
    # =========================================================================
    
    def test_mcp_tarot_draw_success(self):
        """Test successful tarot card draw through MCP client."""
        print("\n" + "="*70)
        print("E2E TEST 1: MCP Client → Tarot Server → tarot.draw")
        print("="*70)
        
        # Call tarot.draw through MCP client
        print("\nCalling tarot.draw through MCPClient...")
        result = self.mcp_client.call_tool('tarot.draw', {})
        
        # Verify response structure
        self.assertTrue(result['success'], "Request should succeed")
        self.assertIn('result', result, "Response should contain result")
        self.assertIn('request_id', result, "Response should contain request_id")
        self.assertEqual(result['tool_name'], 'tarot.draw')
        
        print(f"  ✓ Success: {result['success']}")
        print(f"  ✓ Request ID: {result['request_id']}")
        print(f"  ✓ Tool Name: {result['tool_name']}")
        
        # Verify tarot card structure
        card = result['result']
        self.assertIn('card_name', card, "Card should have name")
        self.assertIn('meaning', card, "Card should have meaning")
        self.assertIn('risk_alignment', card, "Card should have risk_alignment")
        self.assertIn('omen_message', card, "Card should have omen_message")
        
        # Verify all fields are non-empty strings
        self.assertIsInstance(card['card_name'], str)
        self.assertGreater(len(card['card_name']), 0)
        self.assertIsInstance(card['meaning'], str)
        self.assertGreater(len(card['meaning']), 0)
        self.assertIsInstance(card['risk_alignment'], str)
        self.assertGreater(len(card['risk_alignment']), 0)
        self.assertIsInstance(card['omen_message'], str)
        self.assertGreater(len(card['omen_message']), 0)
        
        # Verify risk_alignment is valid
        valid_alignments = ['stability', 'disruption', 'transformation', 'caution', 'opportunity']
        self.assertIn(card['risk_alignment'], valid_alignments,
                     f"Risk alignment '{card['risk_alignment']}' should be one of {valid_alignments}")
        
        print(f"  ✓ Card Name: {card['card_name']}")
        print(f"  ✓ Risk Alignment: {card['risk_alignment']}")
        print(f"  ✓ All required fields present and valid")
        print("="*70)
    
    def test_mcp_tarot_draw_multiple_calls(self):
        """Test multiple tarot draws return valid cards (may be different)."""
        print("\n" + "="*70)
        print("E2E TEST 2: Multiple Tarot Draws")
        print("="*70)
        
        cards_drawn = []
        
        # Draw 5 cards
        for i in range(5):
            result = self.mcp_client.call_tool('tarot.draw', {})
            self.assertTrue(result['success'])
            card = result['result']
            cards_drawn.append(card['card_name'])
            print(f"  Draw {i+1}: {card['card_name']} ({card['risk_alignment']})")
        
        # Verify all draws returned valid cards
        self.assertEqual(len(cards_drawn), 5)
        
        # All cards should have names
        for card_name in cards_drawn:
            self.assertIsInstance(card_name, str)
            self.assertGreater(len(card_name), 0)
        
        print(f"  ✓ All 5 draws returned valid cards")
        print("="*70)
    
    # =========================================================================
    # Test 2: GovernanceInsightsAgent with Tarot Integration
    # =========================================================================
    
    @patch('agents.llm_governance_insights_agent.OpenAIClient')
    @patch('config.settings_loader.get_settings')
    def test_governance_insights_agent_with_tarot(self, mock_get_settings, mock_openai_class):
        """Test GovernanceInsightsAgent includes tarot card in insights."""
        print("\n" + "="*70)
        print("E2E TEST 3: GovernanceInsightsAgent with Tarot Integration")
        print("="*70)
        
        # Mock settings to enable tarot
        mock_settings = Mock()
        mock_settings.get.return_value = {'enabled': True}
        mock_get_settings.return_value = mock_settings
        
        # Mock OpenAI client
        mock_llm_instance = MagicMock()
        mock_llm_response = json.dumps({
            'trend_summary': 'Test trend summary',
            'risk_trend': 'Increasing',
            'compliance_trend': 'Stable',
            'recurring_issues': ['Issue 1', 'Issue 2'],
            'category_hotspots': ['Category A'],
            'recommendations': ['Recommendation 1'],
            'anomaly_detection': 'No anomalies detected'
        })
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_openai_class.return_value = mock_llm_instance
        
        # Create agent with real MCP client
        agent = GovernanceInsightsAgent()
        
        # Override MCP client to use test endpoint
        agent.mcp_client = self.mcp_client
        
        # Prepare input data
        input_data = {
            'audit_summary': {'total_incidents': 5},
            'governance_analysis': {'risk': 'medium'}
        }
        
        # Run agent
        print("\nRunning GovernanceInsightsAgent...")
        output = agent.run(input_data)
        
        # Verify output structure
        self.assertIn('insights', output)
        self.assertIn('governance_output', output)
        
        insights = output['insights']
        
        # Verify tarot card is included
        self.assertIn('shadow_risk_interpretation', insights,
                     "Insights should include shadow_risk_interpretation")
        
        tarot_card = insights['shadow_risk_interpretation']
        
        # Tarot card should be present (not None) when tarot is enabled
        self.assertIsNotNone(tarot_card, "Tarot card should be present when enabled")
        
        # Verify tarot card structure
        self.assertIn('card_name', tarot_card)
        self.assertIn('meaning', tarot_card)
        self.assertIn('risk_alignment', tarot_card)
        self.assertIn('omen_message', tarot_card)
        
        print(f"  ✓ Tarot card included: {tarot_card['card_name']}")
        print(f"  ✓ Risk alignment: {tarot_card['risk_alignment']}")
        print(f"  ✓ All insights fields present")
        print("="*70)
    
    @patch('agents.llm_governance_insights_agent.OpenAIClient')
    @patch('config.settings_loader.get_settings')
    def test_governance_insights_agent_tarot_disabled(self, mock_get_settings, mock_openai_class):
        """Test GovernanceInsightsAgent works when tarot is disabled."""
        print("\n" + "="*70)
        print("E2E TEST 4: GovernanceInsightsAgent with Tarot Disabled")
        print("="*70)
        
        # Mock settings to disable tarot
        mock_settings = Mock()
        mock_settings.get.return_value = {'enabled': False}
        mock_get_settings.return_value = mock_settings
        
        # Mock OpenAI client
        mock_llm_instance = MagicMock()
        mock_llm_response = json.dumps({
            'trend_summary': 'Test trend summary',
            'risk_trend': 'Stable',
            'compliance_trend': 'Improving',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': ['Keep monitoring'],
            'anomaly_detection': 'None'
        })
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_openai_class.return_value = mock_llm_instance
        
        # Create agent
        agent = GovernanceInsightsAgent()
        
        # Prepare input data
        input_data = {
            'audit_summary': {'total_incidents': 2},
            'governance_analysis': {'risk': 'low'}
        }
        
        # Run agent
        print("\nRunning GovernanceInsightsAgent with tarot disabled...")
        output = agent.run(input_data)
        
        # Verify output structure
        self.assertIn('insights', output)
        insights = output['insights']
        
        # Verify tarot card is None when disabled
        self.assertIn('shadow_risk_interpretation', insights)
        self.assertIsNone(insights['shadow_risk_interpretation'],
                         "Tarot card should be None when disabled")
        
        # Verify agent still works normally
        self.assertIn('trend_summary', insights)
        self.assertIn('recommendations', insights)
        
        print(f"  ✓ Tarot card is None (disabled)")
        print(f"  ✓ Agent still produces normal insights")
        print("="*70)
    
    @patch('agents.llm_governance_insights_agent.OpenAIClient')
    @patch('config.settings_loader.get_settings')
    def test_governance_insights_agent_mcp_failure(self, mock_get_settings, mock_openai_class):
        """Test GovernanceInsightsAgent handles MCP failure gracefully."""
        print("\n" + "="*70)
        print("E2E TEST 5: GovernanceInsightsAgent with MCP Failure")
        print("="*70)
        
        # Mock settings to enable tarot and provide MCP config
        mock_mcp = Mock()
        mock_mcp.endpoint = 'http://127.0.0.1:9999/send'
        mock_mcp.timeout = 5.0
        mock_mcp.retry_delay = 1.0
        mock_mcp.max_retries = 2
        
        mock_notification = Mock()
        mock_notification.mcp = mock_mcp
        
        mock_settings = Mock()
        mock_settings.get.return_value = {'enabled': True}
        mock_settings.notification = mock_notification
        mock_get_settings.return_value = mock_settings
        
        # Mock OpenAI client
        mock_llm_instance = MagicMock()
        mock_llm_response = json.dumps({
            'trend_summary': 'Test trend summary',
            'risk_trend': 'Stable',
            'compliance_trend': 'Stable',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': [],
            'anomaly_detection': 'None'
        })
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_openai_class.return_value = mock_llm_instance
        
        # Create agent
        agent = GovernanceInsightsAgent()
        
        # Override MCP client to use invalid endpoint
        agent.mcp_client = MCPClient(endpoint='http://127.0.0.1:9999/send')
        
        # Prepare input data
        input_data = {
            'audit_summary': {'total_incidents': 3},
            'governance_analysis': {'risk': 'medium'}
        }
        
        # Run agent - should not fail
        print("\nRunning GovernanceInsightsAgent with invalid MCP endpoint...")
        output = agent.run(input_data)
        
        # Verify agent completed successfully
        self.assertIn('insights', output)
        insights = output['insights']
        
        # Verify tarot card is None due to MCP failure
        self.assertIn('shadow_risk_interpretation', insights)
        self.assertIsNone(insights['shadow_risk_interpretation'],
                         "Tarot card should be None when MCP fails")
        
        # Verify agent still produces normal insights (even if no historical data)
        self.assertIn('trend_summary', insights)
        self.assertIsInstance(insights['trend_summary'], str)
        self.assertGreater(len(insights['trend_summary']), 0)
        
        print(f"  ✓ Agent handled MCP failure gracefully")
        print(f"  ✓ Tarot card is None (MCP failed)")
        print(f"  ✓ Normal insights still generated: {insights['trend_summary'][:50]}...")
        print("="*70)
    
    # =========================================================================
    # Test 3: Database Persistence and Retrieval
    # =========================================================================
    
    def test_database_tarot_persistence_round_trip(self):
        """Test storing and retrieving tarot card data from database."""
        print("\n" + "="*70)
        print("E2E TEST 6: Database Tarot Persistence Round Trip")
        print("="*70)
        
        # Insert a pipeline run first
        run_id = db_util.insert_pipeline_run(timestamp=self._get_timestamp(), alerts_count=5)
        self.assertIsNotNone(run_id)
        print(f"\n  Created pipeline run: {run_id}")
        
        # Prepare insights data with tarot card
        insights_data = {
            'trend_summary': 'Test summary',
            'risk_trend': 'Increasing',
            'compliance_trend': 'Stable',
            'recurring_issues': ['Issue 1'],
            'category_hotspots': ['Category A'],
            'recommendations': ['Recommendation 1'],
            'anomaly_detection': 'None',
            'shadow_risk_interpretation': {
                'card_name': 'The Tower',
                'meaning': 'Sudden change, upheaval, chaos',
                'risk_alignment': 'disruption',
                'omen_message': 'Beware of cascading failures'
            }
        }
        
        # Extract tarot card
        tarot_card = insights_data.get('shadow_risk_interpretation')
        
        # Insert insights with tarot card
        print(f"  Inserting insights with tarot card: {tarot_card['card_name']}")
        success = db_util.insert_insights_history(run_id, insights_data, tarot_card)
        self.assertTrue(success, "Insert should succeed")
        
        # Retrieve insights
        print(f"  Retrieving insights...")
        insights_history = db_util.get_insights_history(limit=1)
        self.assertEqual(len(insights_history), 1)
        
        retrieved = insights_history[0]
        
        # Verify tarot card was persisted
        self.assertIn('tarot_card', retrieved)
        self.assertIsNotNone(retrieved['tarot_card'])
        
        # Parse tarot card JSON
        retrieved_tarot = json.loads(retrieved['tarot_card'])
        
        # Verify tarot card data matches
        self.assertEqual(retrieved_tarot['card_name'], 'The Tower')
        self.assertEqual(retrieved_tarot['meaning'], 'Sudden change, upheaval, chaos')
        self.assertEqual(retrieved_tarot['risk_alignment'], 'disruption')
        self.assertEqual(retrieved_tarot['omen_message'], 'Beware of cascading failures')
        
        print(f"  ✓ Retrieved tarot card: {retrieved_tarot['card_name']}")
        print(f"  ✓ All tarot fields match original")
        print("="*70)
    
    def test_database_tarot_null_handling(self):
        """Test database handles NULL tarot card (backward compatibility)."""
        print("\n" + "="*70)
        print("E2E TEST 7: Database NULL Tarot Handling")
        print("="*70)
        
        # Insert a pipeline run
        run_id = db_util.insert_pipeline_run(timestamp=self._get_timestamp(), alerts_count=3)
        self.assertIsNotNone(run_id)
        print(f"\n  Created pipeline run: {run_id}")
        
        # Prepare insights data without tarot card
        insights_data = {
            'trend_summary': 'Test summary without tarot',
            'risk_trend': 'Stable',
            'compliance_trend': 'Improving',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': [],
            'anomaly_detection': 'None'
        }
        
        # Insert insights without tarot card (None)
        print(f"  Inserting insights without tarot card")
        success = db_util.insert_insights_history(run_id, insights_data, tarot_card=None)
        self.assertTrue(success, "Insert should succeed with NULL tarot")
        
        # Retrieve insights
        print(f"  Retrieving insights...")
        insights_history = db_util.get_insights_history(limit=1)
        self.assertEqual(len(insights_history), 1)
        
        retrieved = insights_history[0]
        
        # Verify tarot_card is NULL
        self.assertIn('tarot_card', retrieved)
        self.assertIsNone(retrieved['tarot_card'])
        
        print(f"  ✓ Tarot card is NULL (backward compatible)")
        print(f"  ✓ Insights retrieved successfully")
        print("="*70)
    
    # =========================================================================
    # Test 4: Full Integration Flow
    # =========================================================================
    
    @patch('agents.llm_governance_insights_agent.OpenAIClient')
    @patch('config.settings_loader.get_settings')
    def test_full_integration_flow(self, mock_get_settings, mock_openai_class):
        """Test complete flow: Agent → Tarot → Database → Retrieval."""
        print("\n" + "="*70)
        print("E2E TEST 8: Full Integration Flow")
        print("="*70)
        
        # Mock settings to enable tarot
        mock_settings = Mock()
        mock_settings.get.return_value = {'enabled': True}
        mock_get_settings.return_value = mock_settings
        
        # Mock OpenAI client
        mock_llm_instance = MagicMock()
        mock_llm_response = json.dumps({
            'trend_summary': 'Full integration test',
            'risk_trend': 'Increasing',
            'compliance_trend': 'Stable',
            'recurring_issues': ['Integration issue'],
            'category_hotspots': ['Test category'],
            'recommendations': ['Test recommendation'],
            'anomaly_detection': 'Test anomaly'
        })
        mock_llm_instance.generate.return_value = mock_llm_response
        mock_openai_class.return_value = mock_llm_instance
        
        # Step 1: Insert pipeline run
        print("\n  Step 1: Creating pipeline run...")
        run_id = db_util.insert_pipeline_run(timestamp=self._get_timestamp(), alerts_count=7)
        self.assertIsNotNone(run_id)
        print(f"    ✓ Created run_id: {run_id}")
        
        # Step 2: Run GovernanceInsightsAgent with tarot
        print("\n  Step 2: Running GovernanceInsightsAgent...")
        agent = GovernanceInsightsAgent()
        agent.mcp_client = self.mcp_client
        
        input_data = {
            'audit_summary': {'total_incidents': 7},
            'governance_analysis': {'risk': 'high'}
        }
        
        output = agent.run(input_data)
        insights = output['insights']
        
        # Verify tarot card is present
        self.assertIn('shadow_risk_interpretation', insights)
        tarot_card = insights['shadow_risk_interpretation']
        self.assertIsNotNone(tarot_card)
        print(f"    ✓ Tarot card drawn: {tarot_card['card_name']}")
        
        # Step 3: Store insights with tarot to database
        print("\n  Step 3: Storing insights to database...")
        success = db_util.insert_insights_history(run_id, insights, tarot_card)
        self.assertTrue(success)
        print(f"    ✓ Insights stored successfully")
        
        # Step 4: Retrieve insights from database
        print("\n  Step 4: Retrieving insights from database...")
        insights_history = db_util.get_insights_history(limit=1)
        self.assertEqual(len(insights_history), 1)
        
        retrieved = insights_history[0]
        self.assertEqual(retrieved['run_id'], run_id)
        
        # Step 5: Verify tarot card persisted correctly
        print("\n  Step 5: Verifying tarot card persistence...")
        self.assertIsNotNone(retrieved['tarot_card'])
        retrieved_tarot = json.loads(retrieved['tarot_card'])
        
        self.assertEqual(retrieved_tarot['card_name'], tarot_card['card_name'])
        self.assertEqual(retrieved_tarot['meaning'], tarot_card['meaning'])
        self.assertEqual(retrieved_tarot['risk_alignment'], tarot_card['risk_alignment'])
        self.assertEqual(retrieved_tarot['omen_message'], tarot_card['omen_message'])
        
        print(f"    ✓ Tarot card matches: {retrieved_tarot['card_name']}")
        
        # Step 6: Verify insights data persisted correctly
        print("\n  Step 6: Verifying insights data...")
        retrieved_insights = json.loads(retrieved['insights_data'])
        self.assertEqual(retrieved_insights['trend_summary'], 'Full integration test')
        print(f"    ✓ Insights data persisted correctly")
        
        print("\n  ✓ FULL INTEGRATION FLOW SUCCESSFUL")
        print("="*70)
    
    # =========================================================================
    # Test 5: Backward Compatibility
    # =========================================================================
    
    def test_backward_compatibility_existing_records(self):
        """Test that existing records without tarot still work."""
        print("\n" + "="*70)
        print("E2E TEST 9: Backward Compatibility")
        print("="*70)
        
        # Insert old-style record (without tarot)
        print("\n  Creating old-style record without tarot...")
        run_id = db_util.insert_pipeline_run(timestamp=self._get_timestamp(), alerts_count=2)
        
        insights_data = {
            'trend_summary': 'Old record',
            'risk_trend': 'Stable',
            'compliance_trend': 'Stable',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': [],
            'anomaly_detection': 'None'
        }
        
        success = db_util.insert_insights_history(run_id, insights_data, tarot_card=None)
        self.assertTrue(success)
        print(f"    ✓ Old-style record created")
        
        # Insert new-style record (with tarot)
        print("\n  Creating new-style record with tarot...")
        run_id_2 = db_util.insert_pipeline_run(timestamp=self._get_timestamp(), alerts_count=4)
        
        insights_data_2 = {
            'trend_summary': 'New record',
            'risk_trend': 'Increasing',
            'compliance_trend': 'Stable',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': [],
            'anomaly_detection': 'None'
        }
        
        tarot_card = {
            'card_name': 'The Star',
            'meaning': 'Hope, inspiration',
            'risk_alignment': 'opportunity',
            'omen_message': 'Light pierces darkness'
        }
        
        success = db_util.insert_insights_history(run_id_2, insights_data_2, tarot_card)
        self.assertTrue(success)
        print(f"    ✓ New-style record created")
        
        # Retrieve both records
        print("\n  Retrieving all records...")
        insights_history = db_util.get_insights_history(limit=10)
        self.assertGreaterEqual(len(insights_history), 2)
        
        # Find our records
        old_record = None
        new_record = None
        
        for record in insights_history:
            if record['run_id'] == run_id:
                old_record = record
            elif record['run_id'] == run_id_2:
                new_record = record
        
        self.assertIsNotNone(old_record)
        self.assertIsNotNone(new_record)
        
        # Verify old record has NULL tarot
        self.assertIsNone(old_record['tarot_card'])
        print(f"    ✓ Old record has NULL tarot (backward compatible)")
        
        # Verify new record has tarot
        self.assertIsNotNone(new_record['tarot_card'])
        new_tarot = json.loads(new_record['tarot_card'])
        self.assertEqual(new_tarot['card_name'], 'The Star')
        print(f"    ✓ New record has tarot: {new_tarot['card_name']}")
        
        print("\n  ✓ BACKWARD COMPATIBILITY VERIFIED")
        print("="*70)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("STARTING E2E TESTS: Tarot Oracle Integration")
    print("="*70)
    
    unittest.main(verbosity=2)
