"""
LLMAlertSummaryAgent uses an LLM to generate human-friendly summaries of alert events.
This agent sits between MonitorAgent and TriageAgent in the pipeline.
"""
import json
import yaml
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from utils.json_parser import extract_json_block

class LLMAlertSummaryAgent(BaseAgent):
    """
    LLMAlertSummaryAgent analyzes alert events and generates a natural language summary
    using an LLM. It enriches the alert data with contextual insights before triage.
    """
    
    def __init__(self, name: str = "LLMAlertSummaryAgent", model: str = "gpt-4o-mini"):
        """
        Initialize the LLM Alert Summary Agent.
        
        Args:
            name: Agent name for logging
            model: OpenAI model to use for summarization
        """
        super().__init__(name)
        self.llm_client = OpenAIClient(model=model)
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """
        Load the alert summary prompt template from config/prompts.yaml.
        
        Returns:
            str: Prompt template string
        """
        try:
            with open('config/prompts.yaml', 'r') as f:
                prompts = yaml.safe_load(f)
                return prompts.get('alert_summary_prompt', '')
        except Exception as e:
            self.log(f"Warning: Could not load prompt template: {e}")
            # Fallback prompt
            return """You are an AI alert summarizer. Analyze the following alerts (JSON list):
{alerts}

Provide a JSON object with:
- summary: short natural language summary
- categories: list of top categories
- severity_breakdown: mapping of severity->count
- root_causes: list of likely root causes"""
    
    def run(self, input_data: List[Dict]) -> Dict[str, Any]:
        """
        Generate an LLM-powered summary of alert events.
        
        Args:
            input_data: List of alert dictionaries from MonitorAgent
            
        Returns:
            Dict containing:
                - alerts: Original alert list (passed through)
                - llm_summary: LLM-generated summary object with:
                    - summary: Natural language summary
                    - categories: List of alert categories
                    - severity_breakdown: Count by severity level
                    - root_causes: Likely root causes
        """
        self.log("Generating LLM-powered alert summary...")
        
        if not input_data:
            self.log("No alerts to summarize.")
            return {
                'alerts': [],
                'llm_summary': {
                    'summary': 'No alerts detected.',
                    'categories': [],
                    'severity_breakdown': {},
                    'root_causes': []
                }
            }
        
        self.log(f"Processing {len(input_data)} alerts...")
        
        # Prepare alerts for LLM (remove verbose fields)
        simplified_alerts = [
            {
                'timestamp': alert.get('timestamp'),
                'level': alert.get('level'),
                'message': alert.get('message')
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
            llm_summary = self._parse_llm_response(response)
            
            self.log(f"Summary: {llm_summary.get('summary', 'N/A')}")
            self.log(f"Categories: {', '.join(llm_summary.get('categories', []))}")
            
            return {
                'alerts': input_data,
                'llm_summary': llm_summary
            }
            
        except Exception as e:
            self.log(f"Error generating LLM summary: {e}")
            # Return fallback summary
            return {
                'alerts': input_data,
                'llm_summary': self._generate_fallback_summary(input_data)
            }
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured summary.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Dict: Parsed summary object
        """
        parsed = extract_json_block(response)

        if parsed:
            return {
                'summary': parsed.get('summary', 'Summary not available'),
                'categories': parsed.get('categories', []),
                'severity_breakdown': parsed.get('severity_breakdown', {}),
                'root_causes': parsed.get('root_causes', [])
            }

        # fallback mode — keep original Kiro behavior
        self.log("Warning: LLM response was not valid JSON, using fallback")
        return {
            'summary': response[:200] if response else 'No summary available',
            'categories': [],
            'severity_breakdown': {},
            'root_causes': []
        }
    
    def _generate_fallback_summary(self, alerts: List[Dict]) -> Dict[str, Any]:
        """
        Generate a basic summary without LLM when LLM call fails.
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            Dict: Basic summary object
        """
        severity_breakdown = {}
        for alert in alerts:
            level = alert.get('level', 'UNKNOWN')
            severity_breakdown[level] = severity_breakdown.get(level, 0) + 1
        
        return {
            'summary': f"Detected {len(alerts)} alerts across {len(severity_breakdown)} severity levels.",
            'categories': list(severity_breakdown.keys()),
            'severity_breakdown': severity_breakdown,
            'root_causes': ['Analysis unavailable - LLM call failed']
        }
