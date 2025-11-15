from agents.base_agent import BaseAgent

class OpsLogAgent(BaseAgent):
    def run(self, plans):
        self.log("Recording incident log...")
        for plan in plans:
            self.log(f"Incident '{plan['alert']}' → Action: {plan['action']}")
        summary = {"status": "logged", "count": len(plans)}
        self.log(f"Summary: {summary}")
        return summary
