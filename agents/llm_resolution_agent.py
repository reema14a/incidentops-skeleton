"""
LLMResolutionAgent uses an LLM to generate human-friendly remediation summaries.
This agent sits between ResolutionAgent and OpsLogAgent in the pipeline.
"""
import json
import yaml
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from agents.openai_client import OpenAIClient
from utils.json_parser import extract_json_block


class LLMResolutionAgent(BaseAgent):
    """
    LLMResolutionAgent analyzes resolution plans and generates a natural language summary
    using an LLM. It enriches the remediation data with contextual insights and escalation paths.
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
            return """You are an AI incident resolution assistant. Given this list of remediation
actions (JSON):
{actions}

Provide a JSON object with:
- summary: short readable summary for on-call
- recommendations: list of grouped recommended steps
- escalation: suggested escalation paths
- affected_systems: list"""

    
    def run(self, input_data: List[Dict]) -> Dict[str, Any]:
        """
        Generate an LLM-powered summary of resolution plans.
        
        Args:
            input_data: List of resolution plan dictionaries from ResolutionAgent
            
        Returns:
            Dict containing:
                - resolution_plans: Original resolution plans (passed through)
                - llm_resolution_summary: LLM-generated summary object with:
                    - summary: Natural language summary for on-call
                    - recommendations: Grouped recommended steps
                    - escalation: Suggested escalation paths
                    - affected_systems: List of affected systems
        """
        self.log("Generating LLM-powered resolution summary...")
        
        if not input_data:
            self.log("No resolution plans to summarize.")
            return {
                'resolution_plans': [],
                'llm_resolution_summary': {
                    'summary': 'No resolution plans generated.',
                    'recommendations': [],
                    'escalation': 'None required',
                    'affected_systems': []
                }
            }
        
        self.log(f"Processing {len(input_data)} resolution plan(s)...")
        
        # Prepare resolution plans for LLM (simplify structure)
        simplified_plans = [
            {
                'severity': plan.get('severity'),
                'category': plan.get('category'),
                'message': plan.get('message'),
                'recommended_actions': plan.get('recommended_actions', []),
                'priority': plan.get('priority')
            }
            for plan in input_data
        ]
        
        # Format prompt with resolution plans
        prompt = self.prompt_template.format(
            actions=json.dumps(simplified_plans, indent=2)
        )
        
        # Call LLM
        try:
            response = self.llm_client.generate(prompt)
            
            # Parse LLM response
            llm_summary = self._parse_llm_response(response)
            
            self.log(f"Summary: {llm_summary.get('summary', 'N/A')}")
            self.log(f"Escalation: {llm_summary.get('escalation', 'N/A')}")
            
            return {
                'resolution_plans': input_data,
                'llm_resolution_summary': llm_summary
            }
            
        except Exception as e:
            self.log(f"Error generating LLM resolution summary: {e}")
            # Return fallback summary
            return {
                'resolution_plans': input_data,
                'llm_resolution_summary': self._generate_fallback_summary(input_data)
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
                'recommendations': parsed.get('recommendations', []),
                'escalation': parsed.get('escalation', 'No escalation required'),
                'affected_systems': parsed.get('affected_systems', [])
            }

        # fallback mode — keep original Kiro behavior
        self.log("Warning: LLM response was not valid JSON, using fallback")
        return {
            'summary': response[:200] if response else 'No summary available',
            'recommendations': [],
            'escalation': 'Unable to determine',
            'affected_systems': []
        }
    
    def _generate_fallback_summary(self, plans: List[Dict]) -> Dict[str, Any]:
        """
        Generate a basic summary without LLM when LLM call fails.
        
        Args:
            plans: List of resolution plan dictionaries
            
        Returns:
            Dict: Basic summary object
        """
        # Count by severity
        severity_counts = {}
        categories = set()
        
        for plan in plans:
            severity = plan.get('severity', 'unknown')
            category = plan.get('category', 'general')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            categories.add(category)
        
        # Determine escalation based on severity
        escalation = 'None required'
        if 'critical' in severity_counts:
            escalation = 'Immediate escalation to on-call engineer required'
        elif 'high' in severity_counts:
            escalation = 'Consider escalation if issues persist'
        
        return {
            'summary': f"Generated {len(plans)} resolution plan(s) across {len(categories)} categories. Severity breakdown: {severity_counts}",
            'recommendations': ['Review resolution plans', 'Execute recommended actions in priority order'],
            'escalation': escalation,
            'affected_systems': list(categories)
        }
