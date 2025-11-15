def create_incident_ticket(alert, action):
    """Mock JIRA integration."""
    print(f"[JiraHook] Created ticket for '{alert}' with recommended action '{action}'")
