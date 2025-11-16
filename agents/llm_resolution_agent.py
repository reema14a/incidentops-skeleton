"""
LLMResolutionAgent uses an LLM to generate resolution plans and remediation summaries.
This agent sits between TriageAgent and OpsLogAgent in the pipeline.
"""
import json
import yaml
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from utils.json_parser import extract_json_block


class LLMResolutionAgent(BaseAgent):
    """
    LLMResolutionAgent analyzes triaged alerts and generates resolution plans with remediation
    recommendations using an LLM. It provides contextual insights and escalation paths.
    """
    
    def __init__(self, name: str = "LLMResolutionAgent", model: str = "gpt-4o-mini"):
        """
        Initialize the LLM Resolution Agent.
        
        Args:
            name: Agent name for logging
            model: OpenAI model to use for summarization
        """
        super().__init__(name)
        self.llm_client = OpenAIClient(model=model)
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """
        Load the resolution prompt template from config/prompts.yaml.
        
        Returns:
            str: Prompt template string
        """
        try:
            with open('config/prompts.yaml', 'r') as f:
                prompts = yaml.safe_load(f)
                return prompts.get('resolution_prompt', '')
        except Exception as e:
            self.log(f"Warning: Could not load prompt template: {e}")
            # Fallback prompt
            return """You are an AI incident resolution assistant. Given these triaged alerts (JSON):
{alerts}

Analyze each alert and provide a JSON object with:
- resolution_plans: array of objects, each with:
  - alert_id: unique identifier
  - severity: alert severity
  - category: alert category
  - message: alert message
  - recommended_actions: list of specific remediation steps
  - priority: numeric priority (1=highest, 4=lowest)
  - reasoning: explanation for the recommendations
- summary: short readable summary for on-call
- escalation: suggested escalation paths
- affected_systems: list of affected systems"""

    
    def run(self, input_data: List[Dict]) -> Dict[str, Any]:
        """
        Generate LLM-powered resolution plans from triaged alerts.
        
        Args:
            input_data: List of triaged alert dictionaries from TriageAgent
            
        Returns:
            Dict containing:
                - resolution_plans: LLM-generated resolution plans with recommended actions
                - llm_resolution_summary: LLM-generated summary object with:
                    - summary: Natural language summary for on-call
                    - escalation: Suggested escalation paths
                    - affected_systems: List of affected systems
        """
        self.log("Generating LLM-powered resolution plans...")
        
        if not input_data:
            self.log("No alerts to resolve.")
            return {
                'resolution_plans': [],
                'llm_resolution_summary': {
                    'summary': 'No resolution plans generated.',
                    'escalation': 'None required',
                    'affected_systems': []
                }
            }
        
        self.log(f"Processing {len(input_data)} triaged alert(s)...")
        
        # Prepare alerts for LLM
        simplified_alerts = [
            {
                'timestamp': alert.get('timestamp'),
                'severity': alert.get('severity'),
                'category': alert.get('category'),
                'message': alert.get('message'),
                'level': alert.get('level')
            }
            for alert in input_data
        ]
        
        # Format prompt with alerts
        prompt = self.prompt_template.format(
            alerts=json.dumps(simplified_alerts, indent=2)
        )
        
        # Call LLM
        try:
            response = self.llm_client.generate(prompt)
            
            # Parse LLM response
            parsed_output = self._parse_llm_response(response, input_data)
            
            self.log(f"Generated {len(parsed_output['resolution_plans'])} resolution plan(s)")
            self.log(f"Summary: {parsed_output['llm_resolution_summary'].get('summary', 'N/A')}")
            self.log(f"Escalation: {parsed_output['llm_resolution_summary'].get('escalation', 'N/A')}")
            
            return parsed_output
            
        except Exception as e:
            self.log(f"Error generating LLM resolution plans: {e}")
            # Return fallback plans
            return self._generate_fallback_plans(input_data)
    
    def _parse_llm_response(self, response: str, original_alerts: List[Dict]) -> Dict[str, Any]:
        """
        Parse the LLM response into resolution plans and summary.
        
        Args:
            response: Raw LLM response string
            original_alerts: Original triaged alerts for fallback
            
        Returns:
            Dict: Parsed output with resolution_plans and llm_resolution_summary
        """
        parsed = extract_json_block(response)

        if parsed and 'resolution_plans' in parsed:
            return {
                'resolution_plans': parsed.get('resolution_plans', []),
                'llm_resolution_summary': {
                    'summary': parsed.get('summary', 'Summary not available'),
                    'escalation': parsed.get('escalation', 'No escalation required'),
                    'affected_systems': parsed.get('affected_systems', [])
                }
            }

        # fallback mode
        self.log("Warning: LLM response was not valid JSON, using fallback")
        return self._generate_fallback_plans(original_alerts)
    
    def _generate_fallback_plans(self, alerts: List[Dict]) -> Dict[str, Any]:
        """
        Generate basic resolution plans without LLM when LLM call fails.
        
        Args:
            alerts: List of triaged alert dictionaries
            
        Returns:
            Dict: Basic resolution plans and summary
        """
        # Count by severity
        severity_counts = {}
        categories = set()
        resolution_plans = []
        
        # Priority mapping
        priority_map = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        
        for idx, alert in enumerate(alerts):
            severity = alert.get('severity', 'medium')
            category = alert.get('category', 'general')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            categories.add(category)
            
            # Create basic resolution plan
            plan = {
                'alert_id': f"{alert.get('timestamp', 'unknown')}_{idx}",
                'timestamp': alert.get('timestamp'),
                'severity': severity,
                'category': category,
                'message': alert.get('message', ''),
                'recommended_actions': [
                    f"Investigate {category} issue with {severity} severity",
                    "Review system logs for additional context",
                    "Monitor system metrics for related issues"
                ],
                'priority': priority_map.get(severity, 3),
                'reasoning': f"Standard response for {severity} severity {category} incident"
            }
            resolution_plans.append(plan)
        
        # Determine escalation based on severity
        escalation = 'None required'
        if 'critical' in severity_counts:
            escalation = 'Immediate escalation to on-call engineer required'
        elif 'high' in severity_counts:
            escalation = 'Consider escalation if issues persist'
        
        return {
            'resolution_plans': resolution_plans,
            'llm_resolution_summary': {
                'summary': f"Generated {len(resolution_plans)} resolution plan(s) across {len(categories)} categories. Severity breakdown: {severity_counts}",
                'escalation': escalation,
                'affected_systems': list(categories)
            }
        }
