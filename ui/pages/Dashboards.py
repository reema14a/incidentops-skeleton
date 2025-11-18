"""
Dashboards Page

Visualizes incident metrics and trends from pipeline execution history.
Displays severity breakdown, category distribution, and timeline charts.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import database utilities
from db.db_util import (
    get_dashboard_metrics,
    get_pipeline_runs,
    get_severity_distribution,
    get_category_distribution,
    get_timeline_data
)

# Import reusable chart components
from ui.components.charts import (
    render_severity_chart,
    render_category_chart,
    render_timeline_chart
)


def load_resolution_plans_from_db() -> List[Dict[str, Any]]:
    """
    Load resolution plans from database audit data for insights calculation.
    
    This function retrieves resolution plans from the audit_data JSON column
    to support the insights tab calculations.
    
    Returns:
        List[Dict]: List of resolution plan records
    """
    import json
    
    try:
        # Get pipeline runs from database
        db_runs = get_pipeline_runs()
        
        if not db_runs:
            return []
        
        # Import DB connection to query audit_data
        from db.db_util import get_connection
        
        resolution_plans = []
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get all audit_data records
            query = """
                SELECT audit_data
                FROM audit_summary
                WHERE audit_data IS NOT NULL
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                try:
                    audit_data = json.loads(row['audit_data'])
                    plans = audit_data.get('resolution_plans', [])
                    resolution_plans.extend(plans)
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        
        return resolution_plans
        
    except Exception as e:
        st.error(f"Error loading resolution plans from database: {str(e)}")
        return []


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

# Load dashboard metrics from database
metrics = get_dashboard_metrics()

# Handle empty history
if metrics['total_executions'] == 0:
    st.warning("⚠️ No pipeline execution history found in database")
    st.info("Database location: `data/db/incidents.db`")
    st.markdown("""
    **To generate dashboard data:**
    1. Navigate to the **Pipeline Runner** page
    2. Run the pipeline with log input
    3. Return to this page to view visualizations
    """)
    st.stop()

# Display summary statistics from database
st.subheader("📈 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Executions", metrics['total_executions'])

with col2:
    st.metric("Total Incidents", metrics['total_incidents'])

with col3:
    st.metric("Avg Incidents/Run", f"{metrics['avg_incidents_per_run']:.1f}")

with col4:
    # Get most recent execution timestamp
    last_exec = metrics['last_execution_timestamp']
    if last_exec:
        # Extract just the date part if timestamp includes time
        display_date = last_exec.split()[0] if ' ' in last_exec else last_exec.split('T')[0]
        st.metric("Last Execution", display_date)
    else:
        st.metric("Last Execution", "N/A")

st.markdown("---")

# Tabular Navigation for Charts - Insights first as default
tab1, tab2, tab3, tab4 = st.tabs([
    "💡 Insights",
    "🔴 Severity Breakdown",
    "📂 Category Distribution", 
    "📅 Incident Timeline"
])

# Load chart data from database
severity_data = get_severity_distribution()
category_data = get_category_distribution()
timeline_data = get_timeline_data()

# Tab 1: Insights (now first/default)
with tab1:
    if metrics['total_executions'] > 0:
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
            # Calculate average priority from resolution plans stored in DB
            resolution_plans = load_resolution_plans_from_db()
            priorities = []
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
