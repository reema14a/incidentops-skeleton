"""
Incident Intelligence Page

LLM-powered deep insights from LLMGovernanceInsightsAgent
:
- Trend summary
- Tarot interpretation
- Patterns (recurring issues, category hotspots)
- Risk & compliance trends
- Recommendations
- Anomaly detection
"""

import streamlit as st
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
# from datetime import datetime

# Apply global theme
from ui.theme_loader import apply_global_theme, close_sidebar_wrapper
apply_global_theme()

from utils.formatters import format_timestamp
from utils.insights_loader import get_latest_insights
from utils.insights_normalizer import normalize_insights
from ui.components.tarot_preview import render_tarot_card

# Import database utilities
from db import db_util

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.components.charts import (
    render_risk_trend_chart,
    render_compliance_trend_chart
)

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

# def format_timestamp(ts: str) -> str:
#     if not ts or ts == "N/A":
#         return "N/A"
#     try:
#         dt = datetime.fromisoformat(ts.replace("Z", ""))
#         return dt.strftime("%Y-%b-%d %H:%M")
#     except:
#         return ts

def render_list(items):
    for item in items:
        st.markdown(f"- {item}")

def resolve_tarot_image(card_name: str) -> Optional[Path]:
    """
    Resolve tarot card image path from card name.
    
    Converts card name to lowercase, replaces spaces with underscores,
    and searches for .png or .jpeg files in ui/assets.
    
    Args:
        card_name: Name of the tarot card (e.g., "The Tower")
        
    Returns:
        Path to image file if found, None otherwise
    """
    if not card_name:
        return None
    
    # Convert to lowercase
    filename_lower = card_name.lower()
    
    # Try both .png and .jpeg extensions
    assets_dir = Path(__file__).parent.parent / "assets"
    
    # Try with underscores first (preferred convention)
    filename_underscore = filename_lower.replace(" ", "_")
    for ext in [".png", ".jpeg"]:
        image_path = assets_dir / f"{filename_underscore}{ext}"
        if image_path.exists():
            return image_path

    return None

# ---------------------------------------------
# Render Page
# ---------------------------------------------

def render_page():

    # Load Insights
    insights_data = get_latest_insights()
    if not insights_data:
        st.warning("⚠️ No governance insights found in database.")
        st.stop()

    insights = normalize_insights(insights_data['insights'])
    ts = insights_data.get("timestamp", "N/A")
    
    col_title, col_meta = st.columns([5, 2])

    with col_title:
        st.title("🧠 Incident Intelligence")
        st.markdown(
            " "
            "Deep, LLM-powered insights into historical patterns, risks, "
            "compliance trends, and operational behavior across all pipeline runs."
        )

    with col_meta:
        # Add an empty line to push the caption downward into alignment
        st.write("")  
        st.caption(f"Last Analysis: {format_timestamp(ts)}")

    st.markdown("---")
    

    col_left, col_right = st.columns(2)
    # --------------------------
    # Trend Summary (Left)
    # --------------------------
    with col_left:
        st.subheader("📈 Trend Summary")
        render_list(insights.get("trend_summary", []))

        # -------------------------------------
        # Supporting Trend Charts (Expander)
        # -------------------------------------
        with st.expander("📊 Supporting Trend Charts"):
        # st.markdown("### 📊 Supporting Trend Charts")

            # Load DB-backed trend data
            risk_data = get_risk_trend()
            compliance_data = get_compliance_trend()

            # Two tabs
            tab_risk, tab_compliance = st.tabs(["📉 Risk Trend", "📋 Compliance Trend"])

            with tab_risk:
                render_risk_trend_chart(risk_data)

            with tab_compliance:
                render_compliance_trend_chart(compliance_data)

    # --------------------------
    # Tarot (Right)
    # --------------------------
    with col_right:
        st.subheader("🔮 Tarot Interpretation")
        shadow_risk = insights.get("shadow_risk_interpretation")

        # if shadow_risk:
            # # Your existing tarot CSS & layout (unchanged)
            # st.markdown("""
            #     <style>
            #     .tarot-panel {
            #         background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            #         border: 2px solid #9d4edd;
            #         border-radius: 12px;
            #         padding: 0 24px 24px 24px;  /* FIX: remove top padding */
            #         margin: 16px 0;
            #         box-shadow: 0 4px 6px rgba(157, 78, 221, 0.3);
            #     }
            #     .tarot-card-name {
            #         font-size: 24px;
            #         font-weight: bold;
            #         color: #ffd700;
            #         text-align: center;
            #         margin: 16px 0;   /* add spacing since we removed padding */
            #     }
            #     .tarot-meaning {
            #         color: #e0e0e0;
            #         font-size: 14px;
            #         line-height: 1.5;
            #         margin-bottom: 8px;
            #     }
            #     .tarot-omen {
            #         color: #9d4edd;
            #         font-size: 14px;
            #         font-style: italic;
            #         padding: 10px;
            #         background: rgba(157, 78, 221, 0.1);
            #         border-left: 3px solid #9d4edd;
            #         border-radius: 4px;
            #         margin-top: 12px;
            #     }
            #     </style>
            #     """, unsafe_allow_html=True)


            # # st.markdown('<div class="tarot-panel">', unsafe_allow_html=True)
            
            
            # # Display tarot card image
            # card_name = shadow_risk.get("card_name", "")
            # image_path = resolve_tarot_image(card_name)
            
            # if image_path:
            #     st.image(str(image_path), use_container_width=True)
            # else:
            #     # Placeholder for missing image
            #     st.markdown(
            #         f'<div class="tarot-card-name">✨ {shadow_risk.get("card_name", "Unknown Card")} ✨</div>',
            #         unsafe_allow_html=True
            #     )
            #     st.markdown(
            #         """
            #         <div style='text-align:center;padding:40px;background:rgba(157,78,221,0.1);
            #         border-radius:8px;color:#9d4edd;'>
            #             🌙 Card Image Not Available 🌙
            #         </div>
            #         """,
            #         unsafe_allow_html=True
            #     )
            
            # st.markdown(
            #     f'<div class="tarot-meaning"><strong>Meaning:</strong> {shadow_risk.get("meaning")}</div>',
            #     unsafe_allow_html=True
            # )

            # # Risk alignment badge
            # risk_alignment = shadow_risk.get("risk_alignment", "unknown")
            # colors = {
            #     "stability": "#4caf50",
            #     "disruption": "#f44336",
            #     "transformation": "#9c27b0",
            #     "caution": "#ff9800",
            #     "opportunity": "#2196f3"
            # }
            # badge = colors.get(risk_alignment.lower(), "#808080")

            # st.markdown(
            #     f"""
            #     <div style='text-align:center;margin-top:12px;'>
            #         <span style="
            #             background:{badge};color:white;padding:6px 14px;
            #             border-radius:20px;font-weight:bold;">
            #             {risk_alignment}
            #         </span>
            #     </div>
            #     """,
            #     unsafe_allow_html=True,
            # )

            # st.markdown(
            #     f'<div class="tarot-omen"><strong>Omen:</strong> {shadow_risk.get("omen_message")}</div>',
            #     unsafe_allow_html=True,
            # )

            # st.markdown("</div>", unsafe_allow_html=True)

        render_tarot_card(shadow_risk)

        # else:
        #     st.info("No tarot reading available.")

    st.markdown("---")

    # ================================================================
    # 2️⃣ PATTERNS
    # ================================================================
    # st.subheader("🔄 Patterns")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🔁 Recurring Issues")
        render_list(insights.get("recurring_issues", []))
        # if recurring:
        #     for idx, issue in enumerate(recurring, 1):
        #         st.markdown(f"{idx}. {issue}")
        # else:
        #     st.info("No recurring issues identified.")

    with col_right:
        st.markdown("### 🎯 Category Hotspots")
        render_list(insights.get("category_hotspots", []))
        # if hotspots:
        #     for idx, cat in enumerate(hotspots, 1):
        #         st.markdown(f"{idx}. {cat}")
        # else:
        #     st.info("No category hotspots available.")

    st.markdown("---")

    # ================================================================
    # 3️⃣ RISK & COMPLIANCE
    # ================================================================
    # st.subheader("⚖️ Risk & Compliance")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### ⚖️ Risk Trend")
        render_list(insights.get("risk_trend", "No risk trend available."))

    with colB:
        st.markdown("### Compliance Trend")
        render_list(insights.get("compliance_trend", "No compliance trend available."))

    st.markdown("---")

    # ================================================================
    # 4️⃣ ANOMALY DETECTION
    # ================================================================
    st.subheader("🚨 Anomaly Detection")
    anomaly = insights.get("anomaly_detection", [])

    if anomaly:
        for issue in anomaly:
            st.warning(f"- {issue}")
    else:
        st.success("✅ No anomalies detected.")

    st.markdown("---")

    # ================================================================
    # 5️⃣ RECOMMENDATIONS
    # ================================================================
    st.subheader("💡 Recommendations")
    recs = insights.get("recommendations", [])

    if recs:
        for i, r in enumerate(recs, 1):
            st.markdown(f"{i}. {r}")
    else:
        st.info("No recommendations available.")

    st.markdown("---")

    # ================================================================
    # RAW JSON
    # ================================================================
    with st.expander("🔍 View Raw Insights JSON"):
        st.json(insights)


# ---------------------------------------------
if __name__ == "__main__":
    render_page()

# Close sidebar wrapper
close_sidebar_wrapper()
