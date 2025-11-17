"""
Dashboards Page

Visualizes incident metrics and trends from pipeline execution history.
Displays severity breakdown, category distribution, and timeline charts.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

# Import reusable chart components
from ui.components.charts import (
    render_severity_chart,
    render_category_chart,
    render_timeline_chart
)


def get_output_log_path() -> Path:
    """
    Get the path to the output log file.
    
    Returns:
        Path: Path object pointing to data/output/output_log.json
    """
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "output" / "output_log.json"


def load_pipeline_history() -> List[Dict[str, Any]]:
    """
    Load pipeline execution history from output log.
    
    Returns:
        List[Dict]: List of pipeline execution records
    """
    log_path = get_output_log_path()
    
    if not log_path.exists():
        return []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        st.error(f"Error loading pipeline history: {str(e)}")
        return []


def aggregate_severity_data(history: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate severity counts across all pipeline executions.
    
    Args:
        history: List of pipeline execution records
        
    Returns:
        Dict: Severity level to count mapping
    """
    severity_totals = defaultdict(int)
    
    for record in history:
        stage_outputs = record.get('stage_outputs', {})
        triage_stage = stage_outputs.get('triage_stage', {})
        severity_dist = triage_stage.get('severity_distribution', {})
        
        for severity, count in severity_dist.items():
            severity_totals[severity] += count
    
    return dict(severity_totals)


def aggregate_category_data(history: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate category counts across all pipeline executions.
    
    Args:
        history: List of pipeline execution records
        
    Returns:
        Dict: Category to count mapping
    """
    category_totals = defaultdict(int)
    
    for record in history:
        stage_outputs = record.get('stage_outputs', {})
        triage_stage = stage_outputs.get('triage_stage', {})
        category_dist = triage_stage.get('category_distribution', {})
        
        for category, count in category_dist.items():
            category_totals[category] += count
    
    return dict(category_totals)


def extract_timeline_data(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract timeline data from pipeline execution history.
    
    Args:
        history: List of pipeline execution records
        
    Returns:
        List[Dict]: Timeline data with timestamps and incident counts
    """
    timeline = []
    
    for record in history:
        timestamp_str = record.get('execution_timestamp', '')
        total_incidents = record.get('total_incidents', 0)
        
        if timestamp_str:
            try:
                # Parse timestamp
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                timeline.append({
                    'timestamp': dt,
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'incidents': total_incidents
                })
            except ValueError:
                continue
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    return timeline


# Page header with controls
col_title, col_refresh, col_interval = st.columns([6, 1, 1])
with col_title:
    st.title("📊 Dashboards")
with col_refresh:
    st.write("")  # Spacing
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
with col_interval:
    st.write("")  # Spacing
    auto_refresh_interval = st.selectbox(
        "Auto-refresh",
        options=[0, 10, 30, 60, 300],
        format_func=lambda x: "Off" if x == 0 else f"{x}s",
        key="auto_refresh_interval",
        label_visibility="collapsed"
    )

st.markdown("Visualize incident metrics and trends from pipeline execution history.")

# Auto-refresh logic
if auto_refresh_interval > 0:
    import time
    
    # Initialize session state for last refresh time
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = time.time()
    
    # Check if it's time to refresh
    current_time = time.time()
    elapsed = current_time - st.session_state.last_refresh_time
    
    if elapsed >= auto_refresh_interval:
        st.session_state.last_refresh_time = current_time
        st.rerun()
    
    # Display countdown in a compact way
    remaining = auto_refresh_interval - int(elapsed)
    st.info(f"⏱️ Auto-refreshing in {remaining}s", icon="ℹ️")

st.markdown("---")

# Load pipeline history
history = load_pipeline_history()

# Handle empty history
if not history:
    st.warning("⚠️ No pipeline execution history found")
    st.info(f"Expected location: `{get_output_log_path()}`")
    st.markdown("""
    **To generate dashboard data:**
    1. Navigate to the **Pipeline Runner** page
    2. Run the pipeline with log input
    3. Return to this page to view visualizations
    """)
    st.stop()

# Display summary statistics
st.subheader("📈 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Executions", len(history))

with col2:
    total_incidents = sum(record.get('total_incidents', 0) for record in history)
    st.metric("Total Incidents", total_incidents)

with col3:
    avg_incidents = total_incidents / len(history) if history else 0
    st.metric("Avg Incidents/Run", f"{avg_incidents:.1f}")

with col4:
    # Get most recent execution timestamp
    if history:
        latest = history[-1].get('execution_timestamp', 'N/A')
        st.metric("Last Execution", latest.split()[0] if latest != 'N/A' else 'N/A')

st.markdown("---")

# Tabular Navigation for Charts - Insights first as default
tab1, tab2, tab3, tab4 = st.tabs([
    "💡 Insights",
    "🔴 Severity Breakdown",
    "📂 Category Distribution", 
    "📅 Incident Timeline"
])

# Prepare data for all tabs
severity_data = aggregate_severity_data(history)
category_data = aggregate_category_data(history)
timeline_data = extract_timeline_data(history)

# Tab 1: Insights (now first/default)
with tab1:
    if history:
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.markdown("**Most Common Severity:**")
            if severity_data:
                most_common_severity = max(severity_data.items(), key=lambda x: x[1])
                st.write(f"• {most_common_severity[0].capitalize()} ({most_common_severity[1]} incidents)")
            else:
                st.write("• N/A")
            
            st.markdown("**Most Common Category:**")
            if category_data:
                most_common_category = max(category_data.items(), key=lambda x: x[1])
                st.write(f"• {most_common_category[0].capitalize()} ({most_common_category[1]} incidents)")
            else:
                st.write("• N/A")
        
        with insights_col2:
            st.markdown("**Peak Incident Day:**")
            if timeline_data:
                # Group by date and sum incidents
                date_totals = defaultdict(int)
                for item in timeline_data:
                    date_totals[item['date']] += item['incidents']
                
                if date_totals:
                    peak_date = max(date_totals.items(), key=lambda x: x[1])
                    st.write(f"• {peak_date[0]} ({peak_date[1]} incidents)")
                else:
                    st.write("• N/A")
            else:
                st.write("• N/A")
            
            st.markdown("**Average Resolution Priority:**")
            # Calculate average priority from resolution plans
            priorities = []
            for record in history:
                resolution_plans = record.get('resolution_plans', [])
                for plan in resolution_plans:
                    priority = plan.get('priority')
                    if priority is not None:
                        priorities.append(priority)
            
            if priorities:
                avg_priority = sum(priorities) / len(priorities)
                st.write(f"• {avg_priority:.1f}")
            else:
                st.write("• N/A")

# Tab 2: Severity Breakdown
with tab2:
    render_severity_chart(severity_data)

# Tab 3: Category Distribution
with tab3:
    render_category_chart(category_data)

# Tab 4: Incident Timeline
with tab4:
    render_timeline_chart(timeline_data)

# Footer
st.markdown("---")
st.caption("💡 Tip: Charts update automatically when new pipeline executions are recorded.")
