"""Home dashboard — quick overview, import/export, sample data loader."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import load_data, save_data, export_csv, import_csv
from utils.analytics import get_kpis


def _get_data() -> pd.DataFrame:
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()
    return st.session_state["data"]


def show():
    st.header("🏠 Dashboard")
    st.markdown("---")

    df = _get_data()
    kpis = get_kpis(df)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.subheader("Quick Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💸 Total Spent",  f"₹{kpis['total_spent']:,.0f}")
    c2.metric("📦 Total Orders",  kpis["total_orders"])
    c3.metric("📅 This Month",   f"₹{kpis['this_month']:,.0f}")
    c4.metric("⭐ Avg Rating",   f"{kpis['avg_rating']:.1f}/5" if kpis["avg_rating"] else "—")
    c5.metric("🔁 Would Reorder", f"{kpis['reorder_pct']:.0f}% Yes")

    # ── Recent orders ─────────────────────────────────────────────────────────
    st.markdown("---")
    if not df.empty:
        st.subheader("🕐 5 Most Recent Orders")
        recent = df.copy()
        recent["date"] = pd.to_datetime(recent["date"], errors="coerce")
        recent = recent.sort_values("date", ascending=False).head(5)

        disp = recent[["date","meal_type","food_item","platform",
                        "amount_paid","excitement_rating","restaurant_name"]].copy()
        disp["date"]              = disp["date"].dt.strftime("%d %b %Y")
        disp["amount_paid"]       = disp["amount_paid"].apply(
            lambda x: f"₹{x:,.0f}" if pd.notna(x) else "—"
        )
        disp["excitement_rating"] = disp["excitement_rating"].apply(
            lambda x: "⭐" * int(x) if pd.notna(x) else "—"
        )
        disp.columns = ["Date","Meal","Food","Platform","Amount","Rating","Restaurant"]
        st.dataframe(disp, use_container_width=True, hide_index=True)
    else:
        st.info("No orders yet. Use **Add Order** to get started!")

    # ── Data management ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ Data Management")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**📥 Import CSV**")
        uploaded = st.file_uploader("Upload food_orders.csv", type=["csv"],
                                    label_visibility="collapsed")
        if uploaded:
            if st.button("📥 Import", use_container_width=True):
                ok, msg, count = import_csv(uploaded)
                if ok:
                    st.success(f"✅ Imported {count} orders.")
                    st.session_state.pop("data", None)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    with c2:
        st.markdown("**📤 Export All**")
        if not df.empty:
            st.download_button(
                "📥 Download CSV", data=export_csv(df),
                file_name="food_orders_all.csv", mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("No data to export.")

    with c3:
        st.markdown("**🧪 Sample Data**")
        if st.button("🎲 Load 40 Sample Orders", use_container_width=True):
            from utils.sample_data import generate_sample_data
            rows = generate_sample_data(40)
            new_df = pd.DataFrame(rows)
            existing = load_data()
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined.drop_duplicates(subset=["order_id"], keep="last", inplace=True)
            if save_data(combined):
                st.session_state.pop("data", None)
                st.success("✅ Sample data loaded!")
                st.rerun()
            else:
                st.error("❌ Failed to save sample data.")

    # ── Migration hint ────────────────────────────────────────────────────────
    if os.path.exists("data/food_orders.csv"):
        raw = pd.read_csv("data/food_orders.csv", nrows=0)
        old_cols = {"rating", "delivery_charges", "coupon_used",
                    "spicy_level", "mood", "healthy_unhealthy"}
        if old_cols.intersection(raw.columns):
            st.markdown("---")
            st.info(
                "ℹ️ Your CSV has **v1 columns** — the app handles them automatically. "
                "To permanently upgrade the file, run:\n\n"
                "```bash\npython utils/migrate.py\n```"
            )
