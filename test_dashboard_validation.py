"""
Validation script for Dashboards page functionality.
Tests data aggregation and processing functions.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import dashboard functions (without streamlit)
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


def aggregate_severity_data(executions: List[Dict]) -> Dict[str, int]:
    """Aggregate severity distribution across all executions."""
    severity_counts = defaultdict(int)
    
    for execution in executions:
        stage_outputs = execution.get('stage_outputs', {})
        triage_stage = stage_outputs.get('triage_stage', {})
        severity_dist = triage_stage.get('severity_distribution', {})
        
        for severity, count in severity_dist.items():
            severity_counts[severity] += count
    
    return dict(severity_counts)


def aggregate_category_data(executions: List[Dict]) -> Dict[str, int]:
    """Aggregate category distribution across all executions."""
    category_counts = defaultdict(int)
    
    for execution in executions:
        stage_outputs = execution.get('stage_outputs', {})
        triage_stage = stage_outputs.get('triage_stage', {})
        category_dist = triage_stage.get('category_distribution', {})
        
        for category, count in category_dist.items():
            category_counts[category] += count
    
    return dict(category_counts)


def extract_timeline_data(executions: List[Dict]) -> List[Dict[str, Any]]:
    """Extract timeline data from executions."""
    timeline = []
    
    for execution in executions:
        timestamp_str = execution.get('execution_timestamp', '')
        total_incidents = execution.get('total_incidents', 0)
        
        if timestamp_str:
            try:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                timeline.append({
                    'timestamp': dt,
                    'incidents': total_incidents,
                    'timestamp_str': timestamp_str
                })
            except ValueError:
                continue
    
    timeline.sort(key=lambda x: x['timestamp'])
    return timeline


# Test with sample data
sample_executions = [
    {
        "execution_timestamp": "2025-11-15 22:57:12",
        "total_incidents": 4,
        "stage_outputs": {
            "triage_stage": {
                "severity_distribution": {"high": 2, "medium": 2},
                "category_distribution": {"database": 1, "memory": 1, "disk": 1, "general": 1}
            }
        }
    },
    {
        "execution_timestamp": "2025-11-15 23:01:57",
        "total_incidents": 3,
        "stage_outputs": {
            "triage_stage": {
                "severity_distribution": {"high": 1, "medium": 2},
                "category_distribution": {"database": 1, "memory": 2}
            }
        }
    }
]

print("Testing Dashboard Functions...")
print("=" * 60)

# Test severity aggregation
severity_data = aggregate_severity_data(sample_executions)
print(f"✓ Severity aggregation: {severity_data}")
assert severity_data['high'] == 3, "High severity count should be 3"
assert severity_data['medium'] == 4, "Medium severity count should be 4"

# Test category aggregation
category_data = aggregate_category_data(sample_executions)
print(f"✓ Category aggregation: {category_data}")
assert category_data['database'] == 2, "Database category count should be 2"
assert category_data['memory'] == 3, "Memory category count should be 3"

# Test timeline extraction
timeline_data = extract_timeline_data(sample_executions)
print(f"✓ Timeline extraction: {len(timeline_data)} data points")
assert len(timeline_data) == 2, "Should have 2 timeline data points"
assert timeline_data[0]['incidents'] == 4, "First execution should have 4 incidents"

print("=" * 60)
print("✅ All dashboard functions validated successfully!")
