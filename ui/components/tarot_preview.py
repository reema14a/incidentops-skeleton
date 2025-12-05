import streamlit as st
from pathlib import Path

# Utility: resolves tarot image filename from card name
def resolve_tarot_image(card_name: str) -> Path | None:
    if not card_name:
        return None

    filename = card_name.lower().replace(" ", "_")
    assets_dir = Path(__file__).resolve().parents[1] / "assets"

    for ext in [".png", ".jpeg"]:
        candidate = assets_dir / f"{filename}{ext}"
        if candidate.exists():
            return candidate

    return None

def get_risk_color(alignment: str) -> str:
    colors = {
        "stability": "#4caf50",
        "disruption": "#f44336",
        "transformation": "#9c27b0",
        "caution": "#ff9800",
        "opportunity": "#2196f3"
    }
    return colors.get((alignment or "").lower(), "#808080")

# ---------------------------------------------------------------------------
# 1️⃣ DASHBOARD / HOME — COMPACT TAROT PREVIEW
# ---------------------------------------------------------------------------
def render_tarot_preview(shadow_risk: dict):
    """
    Compact tarot preview used in Dashboard and Home pages.
    Text only, minimal footprint, short meaning excerpt.
    """

    if not shadow_risk:
        st.info("✨ Your Tarot reading will appear here after the next pipeline run.")
        return

    card_name = shadow_risk.get("card_name", "Unknown Card")

    image_path = resolve_tarot_image(card_name)
    
    meaning = shadow_risk.get("meaning", "")
    short_meaning = meaning[:140] + "..." if len(meaning) > 140 else meaning
    alignment = shadow_risk.get("risk_alignment", "").capitalize() or "Unknown"

    color = get_risk_color(alignment)

    # --------------------------
    # Two columns for clean layout
    # --------------------------
    col_text, col_img = st.columns([3, 1])

    with col_text:
        st.markdown(f"**{card_name}**")
        st.markdown(short_meaning)
        st.markdown(
            f"Risk Alignment: "
            f"<span style='color:{color}; font-weight:bold;'>{alignment.capitalize()}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("👉 *View the full interpretation in the [Incident Intelligence](/Incident_Intelligence) page.*")

    with col_img:
        if image_path:
            st.image(str(image_path), width=140)  # small right-side preview
        # If no image → show nothing. No placeholder.


def render_tarot_card(shadow_risk: dict):
    """
    Full tarot card rendering for Incident Intelligence page.
    Shows tarot image, meaning, badge, and omen.
    """

    if not shadow_risk:
        st.info("No tarot reading available.")
        return

    # Your existing tarot CSS & layout (unchanged)
    st.markdown("""
        <style>
        .tarot-panel {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #9d4edd;
            border-radius: 12px;
            padding: 0 24px 24px 24px;  /* FIX: remove top padding */
            margin: 16px 0;
            box-shadow: 0 4px 6px rgba(157, 78, 221, 0.3);
        }
        .tarot-card-name {
            font-size: 24px;
            font-weight: bold;
            color: #ffd700;
            text-align: center;
            margin: 16px 0;   /* add spacing since we removed padding */
        }
        .tarot-meaning {
            color: #e0e0e0;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 8px;
        }
        .tarot-omen {
            color: #9d4edd;
            font-size: 14px;
            font-style: italic;
            padding: 10px;
            background: rgba(157, 78, 221, 0.1);
            border-left: 3px solid #9d4edd;
            border-radius: 4px;
            margin-top: 12px;
        }
        </style>
        """, unsafe_allow_html=True)


    # Display tarot card image
    card_name = shadow_risk.get("card_name", "")
    image_path = resolve_tarot_image(card_name)
    
    if image_path:
        st.image(str(image_path), use_container_width=True)
    else:
        # Placeholder for missing image
        st.markdown(
            f'<div class="tarot-card-name">✨ {shadow_risk.get("card_name", "Unknown Card")} ✨</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div style='text-align:center;padding:40px;background:rgba(157,78,221,0.1);
            border-radius:8px;color:#9d4edd;'>
                🌙 Card Image Not Available 🌙
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown(
        f'<div class="tarot-meaning"><strong>Meaning:</strong> {shadow_risk.get("meaning")}</div>',
        unsafe_allow_html=True
    )

    # Risk alignment badge
    risk_alignment = shadow_risk.get("risk_alignment", "unknown")
    # `colors = {
    #     "stability": "#4caf50",
    #     "disruption": "#f44336",
    #     "transformation": "#9c27b0",
    #     "caution": "#ff9800",
    #     "opportunity": "#2196f3"
    # }
    # badge = colors.get(risk_alignment.lower(), "#808080")
    badge = get_risk_color(risk_alignment)

    st.markdown(
        f"""
        <div style='text-align:center;margin-top:12px;'>
            <span style="
                background:{badge};color:white;padding:6px 14px;
                border-radius:20px;font-weight:bold;">
                {risk_alignment}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="tarot-omen"><strong>Omen:</strong> {shadow_risk.get("omen_message")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)