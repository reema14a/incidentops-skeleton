from orchestrator.orchestrator import run_pipeline

def run(test_mode: bool = False):
    """
    Runs the pipeline in test or console mode.

    Args:
        test_mode (bool): If True, suppress console printing and return summary.
    
    Returns:
        dict: Pipeline summary when test_mode is True.
    """
    summary = run_pipeline()

    if test_mode:
        return summary  # Return summary directly for integration tests
    
    # Normal console output
    print("\n============================================================")
    print("🎯 Pipeline Summary")
    print("============================================================")
    print(summary)
    print("============================================================\n")

    return summary


if __name__ == "__main__":
    print("🚀 Starting IncidentOps pipeline...\n")
    run(test_mode=False)
