"""Search & filter orders — table view with sorting and export."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import load_data, export_csv, export_excel
from utils.helpers import MEAL_TYPES, PLATFORMS


def _get_data() -> pd.DataFrame:
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()
    return st.session_state["data"]


def _apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")

    if f.get("q"):
        q = f["q"].lower()
        d = d[
            d["food_item"].str.lower().str.contains(q, na=False)
            | d["restaurant_name"].str.lower().str.contains(q, na=False)
            | d["platform"].str.lower().str.contains(q, na=False)
            | d["cuisine_type"].str.lower().str.contains(q, na=False)
            | d["remarks"].str.lower().str.contains(q, na=False)
        ]
    if f.get("platforms"):
        d = d[d["platform"].isin(f["platforms"])]
    if f.get("meal_types"):
        d = d[d["meal_type"].isin(f["meal_types"])]
    if f.get("date_from") and f.get("date_to"):
        d = d[
            (d["date"] >= pd.Timestamp(f["date_from"]))
            & (d["date"] <= pd.Timestamp(f["date_to"]))
        ]
    if f.get("min_amt") is not None and f.get("max_amt") is not None:
        d = d[
            (d["amount_paid"] >= f["min_amt"])
            & (d["amount_paid"] <= f["max_amt"])
        ]
    if f.get("min_rating"):
        d = d[d["excitement_rating"] >= f["min_rating"]]
    if f.get("day_type") and f["day_type"] != "All":
        d = d[d["weekday_weekend"] == f["day_type"]]
    if f.get("soa") and f["soa"] != "All":
        d = d[d["should_order_again"] == f["soa"]]
    if f.get("fav_only"):
        d = d[d["favorite"] == "Yes"]
    return d


def show():
    st.header("🔍 Search Orders")
    st.markdown("---")

    df = _get_data()

    # Refresh
    col_h, col_r = st.columns([9, 1])
    with col_r:
        if st.button("🔄 Refresh"):
            st.session_state.pop("data", None)
            st.rerun()

    if df.empty:
        st.info("📭 No orders yet. Add some on the **Add Order** page!")
        return

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.expander("🔎 Filters", expanded=True):
        q = st.text_input("🔍 Keyword search", placeholder="food, restaurant, platform…")

        c1, c2, c3 = st.columns(3)
        with c1:
            sel_platforms  = st.multiselect("📱 Platform",  PLATFORMS)
            sel_meal_types = st.multiselect("🍴 Meal Type", MEAL_TYPES)
        with c2:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            min_d = df["date"].min().date()
            max_d = df["date"].max().date()
            dr = st.date_input("📆 Date Range", value=(min_d, max_d),
                               min_value=min_d, max_value=max_d)
            day_type = st.selectbox("📅 Day Type", ["All", "Weekday", "Weekend"])
        with c3:
            lo = float(df["amount_paid"].min(skipna=True) or 0)
            hi = float(df["amount_paid"].max(skipna=True) or 1000)
            amt_range  = st.slider("💰 Amount (₹)", lo, hi, (lo, hi), step=10.0)
            min_rating = st.slider("⭐ Min Excitement Rating", 1, 5, 1)

        c4, c5 = st.columns(2)
        with c4:
            soa_filter = st.selectbox("🔁 Should Order Again", ["All", "Yes", "No", "Maybe"])
        with c5:
            fav_only = st.checkbox("❤️ Favourites Only")

    filters = dict(
        q=q, platforms=sel_platforms, meal_types=sel_meal_types,
        date_from=dr[0] if len(dr) == 2 else None,
        date_to=dr[1]   if len(dr) == 2 else None,
        min_amt=amt_range[0], max_amt=amt_range[1],
        min_rating=min_rating, day_type=day_type,
        soa=soa_filter, fav_only=fav_only,
    )
    result = _apply_filters(df, filters)

    st.caption(f"**{len(result)}** orders match your filters")

    # ── Export ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "📥 Export CSV", data=export_csv(result),
            file_name="food_orders_export.csv", mime="text/csv",
            use_container_width=True, disabled=result.empty,
        )
    with c2:
        st.download_button(
            "📊 Export Excel", data=export_excel(result),
            file_name="food_orders_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, disabled=result.empty,
        )

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    if result.empty:
        st.warning("No orders match your current filters.")
        return

    DISPLAY_COLS = [
        "date", "meal_type", "food_item", "restaurant_name",
        "platform", "amount_paid", "excitement_rating",
        "should_order_again", "weekday_weekend", "remarks",
    ]
    disp = result[DISPLAY_COLS].copy()
    disp = disp.sort_values("date", ascending=False)
    disp["date"]              = pd.to_datetime(disp["date"]).dt.strftime("%d %b %Y")
    disp["amount_paid"]       = disp["amount_paid"].apply(
        lambda x: f"₹{x:,.0f}" if pd.notna(x) else "—"
    )
    disp["excitement_rating"] = disp["excitement_rating"].apply(
        lambda x: "⭐" * int(x) if pd.notna(x) else "—"
    )
    disp.columns = [
        "Date", "Meal", "Food Item", "Restaurant",
        "Platform", "Amount", "Rating", "Order Again?", "Day Type", "Remarks",
    ]
    st.dataframe(disp, use_container_width=True, height=440, hide_index=True)
