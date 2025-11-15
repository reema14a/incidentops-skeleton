class BaseAgent:
    """Base class for all agents with simple logging."""
    def __init__(self, name):
        self.name = name

    def log(self, message):
        print(f"[{self.name}] {message}")

    def run(self, input_data=None):
        raise NotImplementedError("Each agent must implement its own run() method.")
