import unittest
from ui.console_client import run

class TestFullPipeline(unittest.TestCase):

    def test_full_pipeline_execution(self):
        """
        Ensures the entire IncidentOps pipeline runs end-to-end using sample logs.
        """
        summary = run(test_mode=True)

        self.assertIn("status", summary)
        self.assertEqual(summary["status"], "logged")

        self.assertIn("count", summary)
        self.assertGreater(summary["count"], 0)

        self.assertIn("output_path", summary)
        self.assertTrue(summary["output_path"].startswith("data/"))

        # File validation
        import os
        self.assertTrue(os.path.exists(summary["output_path"]))

