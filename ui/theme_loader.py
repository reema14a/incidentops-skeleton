"""
Global Theme Loader for Streamlit App
Cinematic Mystical Tarot Theme for Kiroween Submission
"""

import streamlit as st
import base64
from pathlib import Path

def load_base64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def apply_global_theme():
    """
    Apply the full dark mystical Kiroween theme.
    Includes:
    - Tailwind + DaisyUI
    - Tarot Guardian background
    - Fog gradient overlay
    - Transparent cards + glowing headers
    - Sidebar mystical gradient styling
    - Sidebar mascot (floating shadow entity)
    """

    # Inject CSS frameworks
    st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.6.0/dist/full.css" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    """, unsafe_allow_html=True)

    # -----------------------------------------------
    # SIDEBAR MASCOT (CORRECT POSITION — DOES NOT OVERLAP MENU)
    # -----------------------------------------------

    # ---------- SIDEBAR MASCOT — Non-blocking, blended, bottom-placed ----------
    # mascot_b64 = load_base64("static/sidebar_mascot.jpeg")

    # st.sidebar.markdown(f"""
    # <style>

    #     /* 1. Correct sidebar content box (NOT the nav container) */
    #     div[data-testid="stSidebarContent"] {{
    #         position: relative;
    #         padding-bottom: 160px; /* space for mascot */
    #     }}

    #     /* 2. Clickable nav items stay above mascot */
    #     div[data-testid="stSidebarContent"] a {{
    #         position: relative;
    #         z-index: 5;
    #     }}

    #     /* 3. Mascot is pinned to bottom-left area of sidebar */
    #     .sidebar-mascot {{
    #         position: absolute;
    #         bottom: 10px;
    #         left: 50%;
    #         transform: translateX(-50%);
    #         width: 120px;

    #         opacity: 0.85;
    #         pointer-events: none;   /* ensures nothing blocks clicks */
    #         z-index: 1;

    #         mix-blend-mode: screen;
    #         filter: drop-shadow(0 0 12px rgba(160, 80, 255, 0.5));

    #         animation: floaty 6s ease-in-out infinite;
    #     }}

    #     @keyframes floaty {{
    #         0%   {{ transform: translateX(-50%) translateY(0px); }}
    #         50%  {{ transform: translateX(-50%) translateY(-8px); }}
    #         100% {{ transform: translateX(-50%) translateY(0px); }}
    #     }}

    # </style>

    # <img class="sidebar-mascot"
    #     src="data:image/jpeg;base64,{mascot_b64}">
    # """, unsafe_allow_html=True)

    # ---------------------------------------
    # SIMPLE + RELIABLE SIDEBAR MASCOT
    # ---------------------------------------

    from PIL import Image

    try:
        mascot = Image.open("static/sidebar_mascot.jpeg")
        st.sidebar.markdown("<br><br><hr>", unsafe_allow_html=True)
        st.sidebar.image(mascot, use_container_width=True)
    except:
        st.sidebar.write("Mascot not found")



    # ---------------------------------------------------
    # MAIN THEME CSS
    # ---------------------------------------------------
    st.markdown("""
    <style>

    /* BACKGROUND IMAGE — TAROT GUARDIAN (ENHANCED VISIBILITY) */
    .stApp {
        background:
            url("assets/tarot_guardian_bg.jpg");
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;

        filter: brightness(1.35) contrast(1.12);
    }

    /* Soft vignette + fog overlay */
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background:
            radial-gradient(
                circle at center,
                rgba(130, 60, 200, 0.10) 0%,
                rgba(30, 0, 60, 0.12) 40%,
                rgba(0, 0, 0, 0.45) 100%
            );
        backdrop-filter: blur(2px);
        pointer-events: none;
        z-index: -1;
    }

    /* Transparent containers */
    .block-container {
        background: transparent !important;
    }

    /* Glowing headers */
    h1, h2, h3, h4 {
        color: #e9d5ff !important;
        text-shadow: 0 0 12px rgba(180,120,255,0.45);
    }

    /* Glass effect on tiles & cards */
    .stButton>button, .stAlert, .stSuccess, .stInfo {
        background: rgba(30, 8, 60, 0.55) !important;
        border: 1px solid rgba(180, 100, 255, 0.25) !important;
        backdrop-filter: blur(6px);
        color: #f3e8ff !important;
    }

    /* Transparent main container */
    [data-testid="stAppViewContainer"] > .main {
        background: transparent !important;
    }

    /* SIDEBAR LINK STYLING */
    [data-testid="stSidebar"] a {
        color: #e9d5ff !important;
        font-weight: 400;
        transition: 0.25s ease;
    }

    [data-testid="stSidebar"] a:hover {
        color: #ffb4ff !important;
        text-shadow: 0 0 8px rgba(255,180,255,0.4);
    }

    [data-testid="stSidebar"] [aria-current="page"] {
        font-weight: 600;
        color: #c084fc !important;
        text-shadow: 0 0 12px rgba(200,132,252,0.6);
    }

    </style>
    """, unsafe_allow_html=True)


def close_sidebar_wrapper():
    """Close the wrapper opened above."""
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
