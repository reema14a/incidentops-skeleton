import streamlit as st

# -----------------------------------------------------
# 📌 Mini Card Wrapper (used for all three snapshot cards)
# -----------------------------------------------------
def mini_card(inner_html: str):
    st.markdown(
        f"""
        <div style="
            background:#eef5ff;
            padding:12px 16px;
            border-radius:12px;
            font-size:13px;
            margin-bottom:8px;
        ">
            {inner_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------
# 🔥 Severity Sparkline Card
# -----------------------------------------------------
def render_mini_severity_card(severity_list):
    if not severity_list:
        severity_text = "N/A → N/A → N/A → N/A → N/A"
    else:
        severity_text = " → ".join(severity_list)

    mini_card(severity_text)


# -----------------------------------------------------
# 🗂 Top 3 Categories Card
# -----------------------------------------------------
def render_mini_categories_card(categories):
    if not categories:
        mini_card("N/A")
        return

    chips = "".join(
        f"""
        <span style="
            background:#eef3ff;
            padding:6px 10px;
            border-radius:12px;
            margin-right:6px;
            font-size:13px;
        ">{cat}</span>
        """ for cat in categories
    )

    mini_card(chips)


# -----------------------------------------------------
# 📅 Last 5 Runs Card
# -----------------------------------------------------
def render_mini_timeline_card(incident_counts):
    if not incident_counts:
        mini_card("N/A")
    else:
        mini_card(", ".join(str(x) for x in incident_counts))
