"""
Reusable Chart Components

Provides reusable chart rendering functions for Streamlit dashboards.
Handles severity breakdown, category distribution, and timeline visualizations.
"""

import streamlit as st
from typing import Dict, List, Any
from collections import defaultdict


def render_severity_chart(severity_data: Dict[str, int]) -> None:
    """
    Render severity breakdown chart with detailed breakdown.
    
    Args:
        severity_data: Dictionary mapping severity levels to counts
    """
    if not severity_data:
        st.info("No severity data available")
        return
    
    # Display as bar chart
    st.bar_chart(severity_data)
    
    # Display detailed breakdown
    with st.expander("View Severity Details"):
        severity_col1, severity_col2 = st.columns(2)
        
        with severity_col1:
            st.markdown("**Severity Counts:**")
            for severity, count in sorted(severity_data.items()):
                severity_label = severity.capitalize()
                if severity.lower() == 'high' or severity.lower() == 'critical':
                    st.error(f"🔴 {severity_label}: {count}")
                elif severity.lower() == 'medium':
                    st.warning(f"🟡 {severity_label}: {count}")
                else:
                    st.success(f"🟢 {severity_label}: {count}")
        
        with severity_col2:
            st.markdown("**Percentage Distribution:**")
            total = sum(severity_data.values())
            for severity, count in sorted(severity_data.items()):
                percentage = (count / total * 100) if total > 0 else 0
                st.write(f"{severity.capitalize()}: {percentage:.1f}%")


def render_category_chart(category_data: Dict[str, int]) -> None:
    """
    Render category distribution chart with detailed breakdown.
    
    Args:
        category_data: Dictionary mapping categories to counts
    """
    if not category_data:
        st.info("No category data available")
        return
    
    # Display as bar chart
    st.bar_chart(category_data)
    
    # Display detailed breakdown
    with st.expander("View Category Details"):
        category_col1, category_col2 = st.columns(2)
        
        with category_col1:
            st.markdown("**Category Counts:**")
            for category, count in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {category.capitalize()}: {count}")
        
        with category_col2:
            st.markdown("**Percentage Distribution:**")
            total = sum(category_data.values())
            for category, count in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                st.write(f"{category.capitalize()}: {percentage:.1f}%")


def render_timeline_chart(timeline_data: List[Dict[str, Any]]) -> None:
    """
    Render incident timeline chart with execution history.
    
    Args:
        timeline_data: List of timeline records with date, time, and incident counts
    """
    if not timeline_data:
        st.info("No timeline data available (timestamps may be missing)")
        return
    
    # Prepare data for line chart
    timeline_dict = {item['date']: item['incidents'] for item in timeline_data}
    
    # Display as line chart
    st.line_chart(timeline_dict)
    
    # Display detailed timeline
    with st.expander("View Timeline Details"):
        st.markdown("**Execution History:**")
        
        for item in reversed(timeline_data[-10:]):  # Show last 10 executions
            st.write(f"• {item['date']} {item['time']}: {item['incidents']} incidents")
        
        if len(timeline_data) > 10:
            st.caption(f"Showing most recent 10 of {len(timeline_data)} executions")
