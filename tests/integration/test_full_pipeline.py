import unittest
from ui.console_client import run

class TestFullPipeline(unittest.TestCase):

    def test_full_pipeline_execution(self):
        """
        Ensures the entire IncidentOps pipeline runs end-to-end using sample logs.
        Tests all 7 stages including LLMGovernanceAgent and NotificationAgent.
        """
        result = run(test_mode=True)

        # Verify notification output structure (final stage)
        self.assertIn("governance_output", result)
        self.assertIn("notification_status", result)
        self.assertIn("notifications_sent", result)
        
        # Verify governance output (passed through from GovernanceAgent)
        governance_output = result["governance_output"]
        self.assertIn("audit_summary", governance_output)
        self.assertIn("governance_analysis", governance_output)
        
        # Verify audit summary
        audit_summary = governance_output["audit_summary"]
        self.assertIn("status", audit_summary)
        self.assertEqual(audit_summary["status"], "logged")

        self.assertIn("count", audit_summary)
        self.assertGreater(audit_summary["count"], 0)

        self.assertIn("output_path", audit_summary)
        self.assertTrue(audit_summary["output_path"].startswith("data/"))

        # File validation
        import os
        self.assertTrue(os.path.exists(audit_summary["output_path"]))
        
        # Verify governance analysis
        governance = governance_output["governance_analysis"]
        self.assertIn("risk", governance)
        self.assertIn(governance["risk"], ["low", "medium", "high", "critical"])
        
        self.assertIn("escalation", governance)
        self.assertIsInstance(governance["escalation"], str)
        
        self.assertIn("compliance_issues", governance)
        self.assertIsInstance(governance["compliance_issues"], list)
        
        self.assertIn("commentary", governance)
        self.assertIsInstance(governance["commentary"], str)
        
        # Verify notification status
        notification_status = result["notification_status"]
        self.assertIn(notification_status, ["success", "partial_failure", "failed", "not_required", "skipped"])
        
        # Verify notifications_sent is a list
        self.assertIsInstance(result["notifications_sent"], list)

