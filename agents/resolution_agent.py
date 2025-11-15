from agents.base_agent import BaseAgent

class ResolutionAgent(BaseAgent):
    def run(self, triaged):
        self.log("Generating remediation plans...")
        plans = []
        for t in triaged:
            action = "Restart DB service" if t["severity"] == "high" else "Investigate logs"
            plans.append({"alert": t["alert"], "action": action})
        self.log("Resolution plans created.")
        return plans
