"""
Deep Governance Insights Page

Displays output from GovernanceInsightsAgent including trend analysis,
recurring issues, category hotspots, compliance trends, risk trends,
recommendations, and anomaly detection.
"""

import streamlit as st
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import database utilities
from db import db_util


def safe_call(fn, *args, default=None, **kwargs):
    """
    Safely call a function and return a default value if it fails.
    
    Args:
        fn: Function to call
        *args: Positional arguments
        default: Default value to return on error
        **kwargs: Keyword arguments
        
    Returns:
        Function result or default value
    """
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default


def get_latest_insights() -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recent governance insights from the database.
    
    Returns:
        Dict: Latest insights data or None if no data exists
    """
    insights_history = safe_call(
        db_util.get_insights_history,
        limit=1,
        default=[]
    )
    
    if not insights_history:
        return None
    
    latest = insights_history[0]
    
    # Parse insights_data JSON
    try:
        insights_data = json.loads(latest['insights_data'])
    except (json.JSONDecodeError, TypeError):
        return None
    
    return {
        'run_id': latest['run_id'],
        'timestamp': latest['timestamp'],
        'insights': insights_data
    }


def format_timestamp(ts: str) -> str:
    """
    Format timestamp for display.
    
    Args:
        ts: ISO format timestamp string
        
    Returns:
        str: Formatted timestamp
    """
    if not ts or ts == "N/A":
        return "N/A"
    try:
        # Remove trailing Z if exists
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        return dt.strftime("%Y-%b-%d %H:%M")
    except:
        return ts  # fallback


def get_risk_trend():
    """Retrieve risk trend data from database."""
    return safe_call(
        db_util.get_risk_trend,
        default=[]
    )


def get_compliance_trend():
    """Retrieve compliance trend data from database."""
    return safe_call(
        db_util.get_compliance_trend,
        default=[]
    )


def get_escalation_text_counts():
    """Retrieve escalation frequency data from database."""
    return safe_call(
        db_util.get_escalation_text_counts,
        default={}
    )


def get_risk_emoji(risk_level: str) -> str:
    """
    Get emoji for risk level display.
    
    Args:
        risk_level: Risk level string (low, medium, high, critical)
        
    Returns:
        str: Emoji representing the risk level
    """
    risk_level = risk_level.lower()
    if risk_level == 'critical':
        return '🔴'
    elif risk_level == 'high':
        return '🟠'
    elif risk_level == 'medium':
        return '🟡'
    else:
        return '🟢'


def render_page():
    """Render the Deep Governance Insights page."""
    
    # Page configuration
    st.title("🔍 Deep Governance Insights")
    st.markdown("Advanced trend analysis, recurring issues, and recommendations from historical governance data.")
    st.markdown("---")
    
    # Get latest insights from database
    insights_data = get_latest_insights()
    
    # Handle empty history
    if not insights_data:
        st.warning("⚠️ No governance insights found in database")
        st.markdown("""
        **To generate governance insights:**
        1. Navigate to the **Pipeline Runner** page
        2. Run the pipeline with log input
        3. The GovernanceInsightsAgent will analyze historical data
        4. Return to this page to view deep insights
        """)
        st.stop()
    
    insights = insights_data['insights']
    
    # ============================================================================
    # HEADER - Run metadata
    # ============================================================================
    st.subheader("📊 Insights Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Pipeline Run ID", f"#{insights_data['run_id']}")
    
    with col2:
        formatted_ts = format_timestamp(insights_data['timestamp'])
        st.metric("Analysis Time", formatted_ts)
    
    st.markdown("---")
    
    # ============================================================================
    # TREND SUMMARY
    # ============================================================================
    st.subheader("📈 Trend Summary")
    
    trend_summary = insights.get('trend_summary', 'No trend summary available')
    st.markdown(trend_summary)
    
    st.markdown("---")
    
    # ============================================================================
    # PATTERNS SECTION
    # ============================================================================
    st.subheader("🔄 Patterns")
    
    # Create tabs for different pattern views
    pattern_tab1, pattern_tab2 = st.tabs([
        "🔁 Recurring Issues",
        "🎯 Category Hotspots"
    ])
    
    # Tab 1: Recurring Issues
    with pattern_tab1:
        recurring_issues = insights.get('recurring_issues', [])
        
        if recurring_issues:
            st.markdown("**Identified Recurring Issues:**")
            for idx, issue in enumerate(recurring_issues, 1):
                st.markdown(f"{idx}. {issue}")
        else:
            st.info("No recurring issues identified")
    
    # Tab 2: Category Hotspots
    with pattern_tab2:
        category_hotspots = insights.get('category_hotspots', [])
        
        if category_hotspots:
            st.markdown("**Frequently Occurring Categories:**")
            for idx, category in enumerate(category_hotspots, 1):
                st.markdown(f"{idx}. {category}")
        else:
            st.info("No category hotspots identified")
    
    st.markdown("---")
    
    # ============================================================================
    # RISK & COMPLIANCE
    # ============================================================================
    st.subheader("⚖️ Risk & Compliance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Risk Trend:**")
        risk_trend = insights.get('risk_trend', 'No risk trend data available')
        st.markdown(risk_trend)
    
    with col2:
        st.markdown("**Compliance Trend:**")
        compliance_trend = insights.get('compliance_trend', 'No compliance trend data available')
        st.markdown(compliance_trend)
    
    st.markdown("---")
    
    # ============================================================================
    # RECOMMENDATIONS
    # ============================================================================
    st.subheader("💡 Recommendations")
    
    recommendations = insights.get('recommendations', [])
    
    if recommendations:
        for idx, recommendation in enumerate(recommendations, 1):
            st.markdown(f"{idx}. {recommendation}")
    else:
        st.info("No recommendations available")
    
    st.markdown("---")
    
    # ============================================================================
    # ANOMALY DETECTION
    # ============================================================================
    st.subheader("🚨 Anomaly Detection")
    
    anomaly_detection = insights.get('anomaly_detection', 'No anomaly detection data available')
    
    if anomaly_detection and anomaly_detection != 'No anomaly detection data available':
        st.warning(anomaly_detection)
    else:
        st.success("✅ No anomalies detected")
    
    st.markdown("---")
    
    # ============================================================================
    # TAROT INTERPRETATION
    # ============================================================================
    st.subheader("🔮 Tarot Interpretation")
    
    shadow_risk = insights.get('shadow_risk_interpretation')
    
    if shadow_risk:
        # Apply mystical styling using custom CSS
        st.markdown("""
        <style>
        .tarot-panel {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #9d4edd;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 4px 6px rgba(157, 78, 221, 0.3);
        }
        .tarot-card-name {
            font-size: 28px;
            font-weight: bold;
            color: #ffd700;
            text-align: center;
            margin-bottom: 16px;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }
        .tarot-meaning {
            color: #e0e0e0;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 12px;
        }
        .tarot-omen {
            color: #9d4edd;
            font-size: 16px;
            font-style: italic;
            line-height: 1.6;
            margin-top: 12px;
            padding: 12px;
            background: rgba(157, 78, 221, 0.1);
            border-left: 3px solid #9d4edd;
            border-radius: 4px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create tarot panel
        st.markdown('<div class="tarot-panel">', unsafe_allow_html=True)
        
        # Card name
        card_name = shadow_risk.get('card_name', 'Unknown Card')
        st.markdown(f'<div class="tarot-card-name">✨ {card_name} ✨</div>', unsafe_allow_html=True)
        
        # Meaning
        meaning = shadow_risk.get('meaning', 'No meaning available')
        st.markdown(f'<div class="tarot-meaning"><strong>Meaning:</strong> {meaning}</div>', unsafe_allow_html=True)
        
        # Risk alignment badge
        risk_alignment = shadow_risk.get('risk_alignment', 'unknown')
        
        # Define risk alignment colors
        risk_colors = {
            'stability': '#4caf50',      # Green
            'disruption': '#f44336',     # Red
            'transformation': '#9c27b0', # Purple
            'caution': '#ff9800',        # Orange
            'opportunity': '#2196f3'     # Blue
        }
        
        badge_color = risk_colors.get(risk_alignment.lower(), '#808080')
        
        st.markdown(f"""
        <div style="text-align: center; margin: 16px 0;">
            <span style="
                background-color: {badge_color};
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            ">
                {risk_alignment}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Omen message
        omen_message = shadow_risk.get('omen_message', 'No omen message available')
        st.markdown(f'<div class="tarot-omen">🌙 <strong>Omen:</strong> {omen_message}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Graceful fallback when no tarot data available
        st.markdown("""
        <div style="
            text-align: center;
            padding: 32px;
            color: #9d4edd;
            font-style: italic;
            background: rgba(157, 78, 221, 0.05);
            border: 1px dashed #9d4edd;
            border-radius: 8px;
        ">
            🌙 No tarot reading available for this insight 🔮
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================================================
    # DB-BACKED TREND CHARTS (OPTIONAL)
    # ============================================================================
    st.subheader("📊 Historical Trend Charts")
    st.markdown("Visualize trends across all pipeline runs using database-backed analytics.")
    
    # Create tabs for different trend views
    trend_tab1, trend_tab2, trend_tab3 = st.tabs([
        "🎯 Risk Trend",
        "📋 Compliance Trend",
        "📢 Escalation Frequency"
    ])
    
    # Tab 1: Risk Trend Chart
    with trend_tab1:
        risk_trend_data = get_risk_trend()
        
        if risk_trend_data:
            # Map risk levels to numeric values for charting
            risk_values = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            
            # Prepare data for line chart
            risk_chart_data = {}
            for record in risk_trend_data:
                date_label = f"{record['date']} {record['time']}"
                risk_chart_data[date_label] = risk_values.get(record['risk'].lower(), 0)
            
            st.line_chart(risk_chart_data)
            
            # Display legend
            st.caption("Risk Levels: 1=Low, 2=Medium, 3=High, 4=Critical")
            
            # Show detailed breakdown
            with st.expander("View Risk Trend Details"):
                for record in reversed(risk_trend_data[-10:]):
                    risk_emoji_trend = get_risk_emoji(record['risk'])
                    st.write(f"• Run #{record['run_id']} ({record['date']} {record['time']}): {risk_emoji_trend} {record['risk'].capitalize()}")
                
                if len(risk_trend_data) > 10:
                    st.caption(f"Showing most recent 10 of {len(risk_trend_data)} records")
        else:
            st.info("No risk trend data available. Run the pipeline multiple times to generate trend data.")
    
    # Tab 2: Compliance Trend Chart
    with trend_tab2:
        compliance_trend_data = get_compliance_trend()
        
        if compliance_trend_data:
            # Prepare data for line chart
            compliance_chart_data = {}
            for record in compliance_trend_data:
                date_label = f"{record['date']} {record['time']}"
                compliance_chart_data[date_label] = record['issue_count']
            
            st.line_chart(compliance_chart_data)
            
            # Show detailed breakdown
            with st.expander("View Compliance Trend Details"):
                for record in reversed(compliance_trend_data[-10:]):
                    icon = "✅" if record['issue_count'] == 0 else "⚠️"
                    st.write(f"• Run #{record['run_id']} ({record['date']} {record['time']}): {icon} {record['issue_count']} issue(s)")
                
                if len(compliance_trend_data) > 10:
                    st.caption(f"Showing most recent 10 of {len(compliance_trend_data)} records")
        else:
            st.info("No compliance trend data available. Run the pipeline multiple times to generate trend data.")
    
    # Tab 3: Escalation Frequency Chart
    with trend_tab3:
        escalation_counts = get_escalation_text_counts()
        
        if escalation_counts:
            # Display as bar chart
            st.bar_chart(escalation_counts)
            
            # Show detailed breakdown
            with st.expander("View Escalation Details"):
                st.markdown("**Escalation Recommendations:**")
                for escalation_text, count in sorted(escalation_counts.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• {escalation_text}: {count} occurrence(s)")
        else:
            st.info("No escalation data available. Run the pipeline multiple times to generate trend data.")
    
    st.markdown("---")
    
    # ============================================================================
    # RAW JSON EXPANDER
    # ============================================================================
    with st.expander("🔍 View Raw Insights JSON", expanded=False):
        st.json(insights)
    
    # Footer
    st.markdown("---")
    st.caption("💡 Tip: Deep Governance Insights are generated by the GovernanceInsightsAgent based on historical governance data.")


if __name__ == "__main__":
    render_page()
