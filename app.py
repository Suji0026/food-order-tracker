"""
🍽️ Food Order Tracker v2
Entry point — sets page config, injects global CSS, and routes pages.
"""
import streamlit as st
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="🍽️ Food Order Tracker",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

/* Background */
.stApp                          { background-color: #0d0d0d; color: #f0f0f0; }

/* Sidebar */
section[data-testid="stSidebar"]{ background-color: #161616 !important;
                                   border-right: 1px solid #262626; }

/* Headings */
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif;
                  font-weight: 700; color: #ffffff; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 0.75rem 1rem;
}
div[data-testid="metric-container"] label { color: #888 !important; font-size: 0.78rem !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"]
                                         { color: #fff !important; font-weight: 600; }

/* Forms */
div[data-testid="stForm"] {
    background: #161616;
    border: 1px solid #252525;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
    border: none; border-radius: 8px;
    color: #fff; font-weight: 600; font-size: 0.95rem;
    transition: opacity .15s, transform .15s;
}
.stButton > button[kind="primary"]:hover {
    opacity: .88; transform: translateY(-1px);
    box-shadow: 0 4px 18px rgba(255,107,107,.4);
}

/* Inputs */
.stTextInput  > div > div,
.stSelectbox  > div > div,
.stNumberInput > div > div { background: #1f1f1f !important; border-color: #333 !important; }

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Divider */
hr { border-color: #252525; }

/* Sidebar nav label */
.sidebar-logo {
    font-size: 1.45rem; font-weight: 700;
    color: #FF6B6B; padding-bottom: 0.25rem;
}
.sidebar-tagline { font-size: 0.68rem; color: #555; margin-bottom: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ────────────────────────────────────────────────────────
PAGES = {
    "🏠 Dashboard":      "dashboard",
    "➕ Add Order":      "add_order",
    "✏️ Edit Order":    "edit_order",
    "🔍 Search Orders": "search_orders",
    "🗑️ Delete Order":  "delete_order",
    "📊 Analytics":     "analytics_page",
    "🤖 AI Assistant":  "ai_assistant",
}

with st.sidebar:
    st.markdown('<div class="sidebar-logo">🍽️ Food Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Personal Order Log — v2</div>', unsafe_allow_html=True)

    page = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

    st.markdown("---")

    # Live record count
    if os.path.exists("data/food_orders.csv"):
        try:
            import pandas as pd
            n = len(pd.read_csv("data/food_orders.csv"))
            st.success(f"📦 {n} orders on record")
        except Exception:
            st.warning("⚠️ Data file unreadable")
    else:
        st.info("No data file yet")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:.68rem;color:#444;line-height:1.6'>"
        "Streamlit · Pandas · Plotly<br>"
        "© 2025 Personal Use"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Page routing ──────────────────────────────────────────────────────────────
module_name = PAGES[page]

if module_name == "dashboard":
    from pages.dashboard      import show
elif module_name == "add_order":
    from pages.add_order      import show
elif module_name == "edit_order":
    from pages.edit_order     import show
elif module_name == "search_orders":
    from pages.search_orders  import show
elif module_name == "delete_order":
    from pages.delete_order   import show
elif module_name == "analytics_page":
    from pages.analytics_page import show
elif module_name == "ai_assistant":
    from pages.ai_assistant   import show

show()
