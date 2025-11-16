"""
LLMGovernanceAgent uses an LLM to perform risk scoring, escalation checks, and compliance analysis.
This agent sits after OpsLogAgent as the final stage in the pipeline.
"""
import json
import yaml
from typing import Dict, Any
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from utils.json_parser import extract_json_block


class LLMGovernanceAgent(BaseAgent):
    """
    LLMGovernanceAgent analyzes the final audit log and performs governance checks
    using an LLM. It provides risk scoring, escalation recommendations, and compliance analysis.
    """
    
    def __init__(self, name: str = "LLMGovernanceAgent", model: str = "gpt-4o-mini"):
        """
        Initialize the LLM Governance Agent.
        
        Args:
            name: Agent name for logging
            model: OpenAI model to use for governance analysis
        """
        super().__init__(name)
        self.llm_client = OpenAIClient(model=model)
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """
        Load the governance prompt template from config/prompts.yaml.
        
        Returns:
            str: Prompt template string
        """
        try:
            with open('config/prompts.yaml', 'r') as f:
                prompts = yaml.safe_load(f)
                return prompts.get('governance_prompt', '')
        except Exception as e:
            self.log(f"Warning: Could not load prompt template: {e}")
            # Fallback prompt
            return """You are an AI governance and compliance auditor. Analyze the following final log summary (JSON):
{log}

Provide a JSON object with:
- risk: one of [low, medium, high, critical]
- escalation: recommended escalation action
- compliance_issues: list (if any)
- commentary: short audit commentary"""
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform governance analysis on the audit log summary.
        
        Args:
            input_data: Dictionary from OpsLogAgent containing:
                - status: Logging status
                - count: Number of incidents
                - timestamp: Execution timestamp
                - output_path: Path to audit log file
            
        Returns:
            Dict containing:
                - audit_summary: Original audit summary (passed through)
                - governance_analysis: LLM-generated governance report with:
                    - risk: Risk level (low, medium, high, critical)
                    - escalation: Recommended escalation action
                    - compliance_issues: List of compliance concerns
                    - commentary: Audit commentary
        """
        self.log("Performing governance and compliance analysis...")
        
        if not input_data or input_data.get('status') == 'no_data':
            self.log("No audit data to analyze.")
            return {
                'audit_summary': input_data,
                'governance_analysis': {
                    'risk': 'low',
                    'escalation': 'None required',
                    'compliance_issues': [],
                    'commentary': 'No incidents detected - system operating normally.'
                }
            }
        
        self.log(f"Analyzing audit log with {input_data.get('count', 0)} incident(s)...")
        
        # Load the full audit log for analysis
        audit_log = self._load_audit_log(input_data.get('output_path'))
        
        if not audit_log:
            self.log("Warning: Could not load audit log, using summary only")
            audit_log = input_data
        
        # Prepare simplified log for LLM
        simplified_log = self._simplify_audit_log(audit_log)
        
        # Format prompt with audit log
        prompt = self.prompt_template.format(
            log=json.dumps(simplified_log, indent=2)
        )
        
        # Call LLM
        try:
            response = self.llm_client.generate(prompt)
            
            # Parse LLM response
            governance_analysis = self._parse_llm_response(response)
            
            self.log(f"Risk Level: {governance_analysis.get('risk', 'N/A')}")
            self.log(f"Escalation: {governance_analysis.get('escalation', 'N/A')}")
            
            if governance_analysis.get('compliance_issues'):
                self.log(f"⚠️  Compliance Issues: {len(governance_analysis['compliance_issues'])}")
            
            return {
                'audit_summary': input_data,
                'governance_analysis': governance_analysis
            }
            
        except Exception as e:
            self.log(f"Error generating governance analysis: {e}")
            # Return fallback analysis
            return {
                'audit_summary': input_data,
                'governance_analysis': self._generate_fallback_analysis(input_data)
            }
    
    def _load_audit_log(self, output_path: str) -> Dict[str, Any]:
        """
        Load the full audit log from file for detailed analysis.
        
        Args:
            output_path: Path to the audit log JSON file
            
        Returns:
            Dict: Latest audit log entry or empty dict if load fails
        """
        if not output_path:
            return {}
        
        try:
            with open(output_path, 'r') as f:
                logs = json.load(f)
                # Return the most recent entry
                if isinstance(logs, list) and logs:
                    return logs[-1]
                elif isinstance(logs, dict):
                    return logs
        except Exception as e:
            self.log(f"Warning: Could not load audit log from {output_path}: {e}")
        
        return {}
    
    def _simplify_audit_log(self, audit_log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplify audit log for LLM analysis by removing verbose fields and adding interpretive summaries.
        
        This method performs interpretation and summarization that OpsLogAgent does not do.
        
        Args:
            audit_log: Full audit log entry
            
        Returns:
            Dict: Simplified audit log with interpretive summaries for LLM
        """
        if not audit_log:
            return {}
        
        # Extract key information for governance analysis
        simplified = {
            'timestamp': audit_log.get('execution_timestamp'),
            'total_incidents': audit_log.get('total_incidents', 0),
            'stage_outputs': audit_log.get('stage_outputs', {})
        }
        
        # Add resolution plan summaries (without full details)
        resolution_plans = audit_log.get('resolution_plans', [])
        if resolution_plans:
            simplified['resolution_plans_summary'] = [
                {
                    'severity': plan.get('severity'),
                    'category': plan.get('category'),
                    'priority': plan.get('priority'),
                    'action_count': len(plan.get('recommended_actions', []))
                }
                for plan in resolution_plans
            ]
            
            # Add interpretive recommendations summary (moved from OpsLogAgent)
            simplified['recommendations_summary'] = self._generate_recommendations_summary(resolution_plans)
        
        return simplified
    
    def _generate_recommendations_summary(self, resolution_plans: list) -> Dict[str, Any]:
        """
        Generate interpretive summary of recommendations for governance analysis.
        
        This interpretive logic was moved from OpsLogAgent to maintain separation of concerns.
        OpsLogAgent records facts; LLMGovernanceAgent interprets them.
        
        Args:
            resolution_plans: List of resolution plan dictionaries
            
        Returns:
            Dict: Interpretive summary of recommendations
        """
        summary = {
            "total_actions": sum(len(plan.get('recommended_actions', [])) for plan in resolution_plans),
            "high_priority_count": sum(1 for plan in resolution_plans if plan.get('priority', 4) <= 2),
            "categories_affected": list(set(plan.get('category', 'unknown') for plan in resolution_plans)),
            "critical_actions": []
        }
        
        # Extract critical actions (priority 1) for governance review
        for plan in resolution_plans:
            if plan.get('priority') == 1:
                summary["critical_actions"].append({
                    "alert_id": plan.get('alert_id'),
                    "category": plan.get('category'),
                    "actions": plan.get('recommended_actions', [])
                })
        
        return summary
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured governance analysis.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Dict: Parsed governance analysis object
        """
        parsed = extract_json_block(response)

        if parsed:
            # Validate risk level
            risk = parsed.get('risk', 'medium').lower()
            if risk not in ['low', 'medium', 'high', 'critical']:
                risk = 'medium'
            
            return {
                'risk': risk,
                'escalation': parsed.get('escalation', 'No escalation required'),
                'compliance_issues': parsed.get('compliance_issues', []),
                'commentary': parsed.get('commentary', 'Analysis completed')
            }

        # fallback mode
        self.log("Warning: LLM response was not valid JSON, using fallback")
        return {
            'risk': 'medium',
            'escalation': 'Unable to determine - manual review recommended',
            'compliance_issues': [],
            'commentary': response[:200] if response else 'No analysis available'
        }
    
    def _generate_fallback_analysis(self, audit_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a basic governance analysis without LLM when LLM call fails.
        
        Args:
            audit_summary: Summary from OpsLogAgent
            
        Returns:
            Dict: Basic governance analysis object
        """
        incident_count = audit_summary.get('count', 0)
        
        # Determine risk level based on incident count
        if incident_count == 0:
            risk = 'low'
            escalation = 'None required'
        elif incident_count <= 2:
            risk = 'low'
            escalation = 'Monitor for recurring patterns'
        elif incident_count <= 5:
            risk = 'medium'
            escalation = 'Review with team lead if issues persist'
        elif incident_count <= 10:
            risk = 'high'
            escalation = 'Escalate to on-call engineer'
        else:
            risk = 'critical'
            escalation = 'Immediate escalation to incident commander required'
        
        return {
            'risk': risk,
            'escalation': escalation,
            'compliance_issues': ['LLM analysis unavailable - manual compliance review recommended'],
            'commentary': f"Detected {incident_count} incident(s). Risk assessment based on incident count. Manual review recommended for detailed compliance analysis."
        }
