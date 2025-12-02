import streamlit as st

def render_tarot_preview(shadow_risk: dict):
    if not shadow_risk:
        st.info("✨ Your Tarot reading will appear here after the next pipeline run.")
        return
    
    card = shadow_risk.get("card_name", "Unknown Card")
    meaning = shadow_risk.get("meaning", "")
    short_meaning = meaning[:140] + "..." if len(meaning) > 140 else meaning
    alignment = shadow_risk.get("risk_alignment", "").capitalize() or "Unknown"

    st.markdown(f"""
    **{card}**  
    {short_meaning}

    **Risk Alignment:** {alignment}

    **👉 View more in the [Incident Intelligence](/Deep_Governance_Insights) page.**
    """)
