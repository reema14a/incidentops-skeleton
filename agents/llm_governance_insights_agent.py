"""
GovernanceInsightsAgent uses an LLM to analyze historical governance data.
This agent sits after LLMGovernanceAgent and provides trend analysis and recommendations.
"""
import json
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from llm.mcp_client import MCPClient, MCPError
from utils.json_parser import extract_json_block
from utils.prompt_loader import load_prompt
from db import db_util


class LLMGovernanceInsightsAgent(BaseAgent):
    """
    GovernanceInsightsAgent analyzes historical governance data from the database
    and provides trend analysis, recurring issue detection, and recommendations.
    
    This agent:
    - Retrieves aggregated historical data using DB utility functions
    - Passes the aggregated data to an LLM for interpretation
    - Returns structured insights for UI display and decision support
    """
    
    def __init__(self, name: str = "GovernanceInsightsAgent", model: str = "gpt-4o-mini"):
        """
        Initialize the Governance Insights Agent.
        
        Args:
            name: Agent name for logging
            model: OpenAI model to use for insights analysis
        """
        super().__init__(name)
        self.llm_client = OpenAIClient(model=model)
        
        # Initialize MCP client for tarot integration
        try:
            self.mcp_client = MCPClient()
            self.log("MCP client initialized for tarot integration")
        except Exception as e:
            self.log(f"Warning: Failed to initialize MCP client: {e}")
            self.mcp_client = None
        
        # Load prompt template
        self.prompt_template = load_prompt('governance_insights_prompt')
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze historical governance data and generate insights.
        
        Args:
            input_data: Dictionary from LLMGovernanceAgent containing:
                - audit_summary: Audit summary from OpsLogAgent
                - governance_analysis: Governance analysis from LLMGovernanceAgent
            
        Returns:
            Dict containing:
                - governance_output: Original governance output (passed through)
                - insights: LLM-generated insights with:
                    - trend_summary: High-level description of patterns
                    - risk_trend: Observations about risk level changes
                    - compliance_trend: How compliance issues have evolved
                    - recurring_issues: List of recurring themes
                    - category_hotspots: Frequently occurring categories/severities
                    - recommendations: Actionable recommendations
                    - anomaly_detection: Abnormalities or outliers
                    - shadow_risk_interpretation: Tarot card data (optional)
        """
        self.log("Analyzing historical governance data...")
        
        # -----------------------------------------------------
        # STEP 1 — Retrieve historical data
        # -----------------------------------------------------
        # Retrieve aggregated historical data from database
        historical_data = self._retrieve_historical_data()
        tarot_card = None

        if not historical_data or not historical_data.get('has_data'):
            self.log("Insufficient historical data for analysis")
            insights = self._generate_no_data_insights()
            insights['shadow_risk_interpretation'] = tarot_card
            return {
                'governance_output': input_data,
                'insights': insights
            }
        
        self.log(f"Retrieved historical data: {historical_data['summary']}")
        
        # -----------------------------------------------------
        # STEP 2 — Generate insights using LLM
        # -----------------------------------------------------
        prompt = self.prompt_template.format(
            historical_data=json.dumps(historical_data, indent=2)
        )
        
        # Call LLM for insights analysis
        try:
            response = self.llm_client.generate(prompt)
            
            # Parse LLM response
            insights = self._parse_llm_response(response)
            
            # -----------------------------------------------------
            # STEP 3 — tarot *AFTER* insights exist
            # -----------------------------------------------------
            tarot_card = self._draw_tarot_card(insights)
            # Include tarot card data in insights
            insights['shadow_risk_interpretation'] = tarot_card
            
            self.log(f"Generated insights: {insights.get('trend_summary', 'N/A')[:100]}...")
            
            if insights.get('recommendations'):
                self.log(f"📊 Generated {len(insights['recommendations'])} recommendation(s)")
            
            if tarot_card:
                self.log(f"🔮 Tarot reading: {tarot_card.get('card_name', 'Unknown')}")
            
            return {
                'governance_output': input_data,
                'insights': insights
            }
            
        except Exception as e:
            self.log(f"Error generating insights: {e}")
            # Return fallback insights
            fallback_insights = self._generate_fallback_insights(historical_data)
            fallback_insights['shadow_risk_interpretation'] = tarot_card
            return {
                'governance_output': input_data,
                'insights': fallback_insights
            }
    
    def _draw_tarot_card(self, insights: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Draw a tarot card through MCP client, using insights to pick the right card.
        """
        insights = insights or {}

        # Check tarot config
        try:
            from config.settings_loader import get_settings
            settings = get_settings()
            tarot_enabled = settings.get('tarot', {}).get('enabled', False)
            if not tarot_enabled:
                self.log("Tarot reading disabled in configuration")
                return None
        except Exception as e:
            self.log(f"Tarot config load failed: {e}")
            return None

        if not self.mcp_client:
            self.log("MCP client not available for tarot")
            return None

        try:
            self.log("Drawing tarot card using insights…")

            # Pass insights into tool call
            response = self.mcp_client.call_tool('tarot.draw', {
                "insights": insights
            })

            if response.get("success") and response.get("result"):
                tarot_data = response['result']
                self.log(f"🔮 Drew tarot card: {tarot_data.get('card_name', 'Unknown')}")
                return tarot_data
            else:
                err = response.get("error", {}).get("message", "Unknown error")
                self.log(f"Tarot draw failed: {err}")
                return None
        except MCPError as e:
            self.log(f"Warning: MCP error during tarot draw: {e.message}")
            return None
        except Exception as e:
            self.log(f"Warning: Unexpected error during tarot draw: {e}")
            return None

    
    def _retrieve_historical_data(self) -> Dict[str, Any]:
        """
        Retrieve aggregated historical data from the database.
        
        This method calls DB utility functions to get aggregated data
        and packages it for LLM analysis.
        
        Returns:
            Dict: Aggregated historical data with keys:
                - has_data: Boolean indicating if sufficient data exists
                - summary: Human-readable summary of data retrieved
                - risk_trend: List of risk levels over time
                - compliance_trend: List of compliance issue counts over time
                - escalation_counts: Dictionary of escalation text frequencies
                - recent_runs: List of recent pipeline run metadata
                - category_distribution: Dictionary of category frequencies
                - severity_distribution: Dictionary of severity frequencies
        """
        try:
            # Get risk trend data
            risk_trend = db_util.get_risk_trend()
            
            # Get compliance trend data
            compliance_trend = db_util.get_compliance_trend()
            
            # Get escalation text counts
            escalation_counts = db_util.get_escalation_text_counts()
            
            # Get recent runs (last 10)
            recent_runs = db_util.get_recent_runs(limit=10)
            
            # Get category distribution
            category_distribution = db_util.get_category_distribution()
            
            # Get severity distribution
            severity_distribution = db_util.get_severity_distribution()
            
            # Check if we have sufficient data
            has_data = (
                len(risk_trend) > 0 or
                len(compliance_trend) > 0 or
                len(recent_runs) > 0
            )
            
            # Build summary
            summary = (
                f"{len(recent_runs)} recent runs, "
                f"{len(risk_trend)} risk assessments, "
                f"{len(compliance_trend)} compliance records"
            )
            
            return {
                'has_data': has_data,
                'summary': summary,
                'risk_trend': risk_trend,
                'compliance_trend': compliance_trend,
                'escalation_counts': escalation_counts,
                'recent_runs': self._simplify_recent_runs(recent_runs),
                'category_distribution': category_distribution,
                'severity_distribution': severity_distribution
            }
            
        except Exception as e:
            self.log(f"Error retrieving historical data: {e}")
            return {
                'has_data': False,
                'summary': 'Error retrieving data',
                'error': str(e)
            }
    
    def _simplify_recent_runs(self, recent_runs: list) -> list:
        """
        Simplify recent runs data for LLM analysis.
        
        Extracts key information from recent runs without overwhelming the LLM
        with full JSON payloads.
        
        Args:
            recent_runs: List of recent run dictionaries from DB
            
        Returns:
            List: Simplified run summaries
        """
        simplified = []
        
        for run in recent_runs:
            run_summary = {
                'run_id': run.get('run_id'),
                'timestamp': run.get('timestamp'),
                'alerts_count': run.get('alerts_count')
            }
            
            # Extract governance data if available
            if run.get('governance_data'):
                try:
                    gov_data = json.loads(run['governance_data'])
                    run_summary['risk'] = gov_data.get('risk')
                    run_summary['escalation_category'] = gov_data.get('escalation_category')
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Extract audit data if available
            if run.get('audit_data'):
                try:
                    audit_data = json.loads(run['audit_data'])
                    run_summary['total_incidents'] = audit_data.get('total_incidents')
                except (json.JSONDecodeError, TypeError):
                    pass
            
            simplified.append(run_summary)
        
        return simplified
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        parsed = extract_json_block(response)

        required_list_fields = [
            'trend_summary',
            'risk_trend',
            'compliance_trend',
            'recurring_issues',
            'category_hotspots',
            'recommendations',
            'anomaly_detection'
        ]

        if parsed:
            # Ensure required fields exist
            for field in required_list_fields:
                if field not in parsed:
                    parsed[field] = []

            # Structural normalization (no sanitization)
            for field in required_list_fields:

                # Convert single string → list of 1
                if isinstance(parsed[field], str):
                    parsed[field] = [parsed[field]]

                # Ensure list items are strings
                if isinstance(parsed[field], list):
                    parsed[field] = [
                        str(item).strip()
                        for item in parsed[field]
                        if isinstance(item, (str, int, float)) and str(item).strip()
                    ]

            return parsed

        # Fallback
        self.log("Warning: LLM response was not valid JSON, using fallback")
        return {
            'trend_summary': [response[:200]] if response else ['No analysis available'],
            'risk_trend': ['Unable to parse'],
            'compliance_trend': ['Unable to parse'],
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': ['Manual review recommended - LLM response parsing failed'],
            'anomaly_detection': ['Unable to parse']
        }

    def _generate_no_data_insights(self) -> Dict[str, Any]:
        """
        Generate insights when insufficient historical data exists.
        
        Returns:
            Dict: Default insights object
        """
        return {
            'trend_summary': 'Insufficient historical data for trend analysis. This is likely the first or second pipeline run.',
            'risk_trend': 'No historical risk data available',
            'compliance_trend': 'No historical compliance data available',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': [
                'Continue running the pipeline to build historical data',
                'Review current governance analysis for immediate concerns'
            ],
            'anomaly_detection': 'Insufficient data for anomaly detection'
        }
    
    def _generate_fallback_insights(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate basic insights without LLM when LLM call fails.
        
        Args:
            historical_data: Historical data retrieved from database
            
        Returns:
            Dict: Basic insights object
        """
        # Extract basic statistics
        risk_trend_data = historical_data.get('risk_trend', [])
        compliance_trend_data = historical_data.get('compliance_trend', [])
        escalation_counts = historical_data.get('escalation_counts', {})
        
        # Determine most common risk level
        risk_levels = [r.get('risk') for r in risk_trend_data if r.get('risk')]
        most_common_risk = max(set(risk_levels), key=risk_levels.count) if risk_levels else 'unknown'
        
        # Determine compliance trend direction
        if len(compliance_trend_data) >= 2:
            recent_issues = compliance_trend_data[-1].get('issue_count', 0)
            older_issues = compliance_trend_data[0].get('issue_count', 0)
            if recent_issues > older_issues:
                compliance_direction = 'increasing'
            elif recent_issues < older_issues:
                compliance_direction = 'decreasing'
            else:
                compliance_direction = 'stable'
        else:
            compliance_direction = 'insufficient data'
        
        # Get most common escalation
        most_common_escalation = max(escalation_counts.items(), key=lambda x: x[1])[0] if escalation_counts else 'None'
        
        return {
            'trend_summary': f'Historical analysis based on {len(risk_trend_data)} runs. Most common risk level: {most_common_risk}. Compliance trend: {compliance_direction}.',
            'risk_trend': f'Most common risk level: {most_common_risk} across {len(risk_trend_data)} assessments',
            'compliance_trend': f'Compliance issues trend: {compliance_direction}',
            'recurring_issues': [f'Most common escalation: {most_common_escalation}'],
            'category_hotspots': list(historical_data.get('category_distribution', {}).keys())[:3],
            'recommendations': [
                'LLM analysis unavailable - manual review recommended',
                f'Focus on {most_common_risk} risk scenarios',
                'Review compliance trend for patterns'
            ],
            'anomaly_detection': 'LLM analysis unavailable - manual anomaly detection recommended'
        }
