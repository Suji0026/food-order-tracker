"""Analytics dashboard with dynamic filters."""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import load_data
from utils.helpers import MEAL_TYPES, PLATFORMS, CUISINE_TYPES
from utils.analytics import (
    filter_data, get_kpis,
    spending_by_month, spending_by_platform, meal_type_distribution,
    weekday_vs_weekend, top_food_items, rating_distribution,
    spending_by_day_of_week, avg_spend_by_meal,
    should_order_again_distribution, spending_by_cuisine,
)

PALETTE = ["#FF6B6B", "#FFA07A", "#FFD93D", "#6BCB77",
           "#4D96FF", "#C77DFF", "#FF85A1", "#00C9B1"]
THEME   = "plotly_dark"


def _get_data() -> pd.DataFrame:
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()
    return st.session_state["data"]


def _chart(fig, height=300):
    fig.update_layout(margin=dict(l=0, r=0, t=24, b=0), height=height)
    st.plotly_chart(fig, use_container_width=True)


def show():
    st.header("📊 Analytics Dashboard")
    st.markdown("---")

    df = _get_data()
    if df.empty:
        st.info("📭 No data yet — add or load sample orders first.")
        return

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ── Dynamic filters ───────────────────────────────────────────────────────
    with st.expander("🔍 Filter Analytics", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            min_d = df["date"].min().date()
            max_d = df["date"].max().date()
            date_from = st.date_input("From Date", value=min_d, min_value=min_d, max_value=max_d)
        with c2:
            date_to = st.date_input("To Date", value=max_d, min_value=min_d, max_value=max_d)
        with c3:
            sel_meals     = st.multiselect("🍴 Meal Type", MEAL_TYPES)
            sel_platforms = st.multiselect("📱 Platform",  PLATFORMS)
        with c4:
            day_type   = st.selectbox("📅 Day Type", ["All", "Weekday", "Weekend"])
            # Cuisines present in data
            known_cui = sorted(df["cuisine_type"].dropna().unique().tolist())
            sel_cui   = st.multiselect("🌍 Cuisine", known_cui)

    fdf = filter_data(
        df,
        date_from=date_from, date_to=date_to,
        meal_types=sel_meals or None,
        platforms=sel_platforms or None,
        day_type=day_type,
        cuisines=sel_cui or None,
    )

    if fdf.empty:
        st.warning("⚠️ No data matches the selected filters.")
        return

    kpis = get_kpis(fdf)

    # ── KPI row 1 ─────────────────────────────────────────────────────────────
    st.subheader("🏆 Key Metrics")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💸 Total Spent",   f"₹{kpis['total_spent']:,.0f}")
    c2.metric("📦 Total Orders",   kpis["total_orders"])
    c3.metric("📅 This Month",     f"₹{kpis['this_month']:,.0f}")
    c4.metric("💰 Avg Order",      f"₹{kpis['avg_order']:,.0f}")
    c5.metric("⭐ Avg Rating",     f"{kpis['avg_rating']:.1f} / 5")

    # ── KPI row 2 ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📱 Top Platform",   kpis["top_platform"])
    c2.metric("🍛 Top Food",       kpis["top_food"])
    c3.metric("🌙 Weekend Spend",  f"₹{kpis['weekend_spend']:,.0f}")
    c4.metric("🔁 Would Reorder",  f"{kpis['reorder_pct']:.0f}% Yes")
    fav_cnt = (fdf["favorite"].astype(str) == "Yes").sum()
    c5.metric("❤️ Favourites",     fav_cnt)

    st.markdown("---")

    # ── Row 1 charts ──────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📅 Monthly Spending")
        mdata = spending_by_month(fdf)
        if not mdata.empty:
            _chart(px.bar(mdata, x="month", y="amount_paid",
                          labels={"month": "Month", "amount_paid": "Amount (₹)"},
                          color_discrete_sequence=[PALETTE[3]], template=THEME))

    with c2:
        st.subheader("📱 Spending by Platform")
        pdata = spending_by_platform(fdf)
        if not pdata.empty:
            _chart(px.pie(pdata, values="amount_paid", names="platform",
                          color_discrete_sequence=PALETTE, template=THEME))

    # ── Row 2 charts ──────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🍴 Meal Type Distribution")
        mtype = meal_type_distribution(fdf)
        if not mtype.empty:
            _chart(px.pie(mtype, values="count", names="meal_type",
                          hole=0.4, color_discrete_sequence=PALETTE, template=THEME))
    with c2:
        st.subheader("⭐ Excitement Rating Distribution")
        rdata = rating_distribution(fdf)
        if not rdata.empty:
            _chart(px.bar(rdata, x="rating", y="count",
                          labels={"rating": "Rating", "count": "Orders"},
                          color_discrete_sequence=[PALETTE[0]], template=THEME))

    # ── Row 3 charts ──────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📅 Spending by Day of Week")
        dow = spending_by_day_of_week(fdf)
        if not dow.empty:
            _chart(px.bar(dow, x="day", y="amount_paid",
                          labels={"day": "", "amount_paid": "Amount (₹)"},
                          color_discrete_sequence=[PALETTE[4]], template=THEME))
    with c2:
        st.subheader("🏆 Top 10 Food Items")
        top = top_food_items(fdf, 10)
        if not top.empty:
            _chart(px.bar(top, x="count", y="food_item", orientation="h",
                          labels={"food_item": "", "count": "Orders"},
                          color_discrete_sequence=[PALETTE[1]], template=THEME))

    # ── Row 4 charts ──────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Weekday vs Weekend Spending")
        wdwe = weekday_vs_weekend(fdf)
        if not wdwe.empty:
            _chart(px.bar(wdwe, x="weekday_weekend", y="total",
                          labels={"weekday_weekend": "", "total": "Total Spend (₹)"},
                          color="weekday_weekend",
                          color_discrete_sequence=[PALETTE[2], PALETTE[0]],
                          template=THEME, text_auto=True))
    with c2:
        st.subheader("🔁 Should Order Again?")
        soa = should_order_again_distribution(fdf)
        if not soa.empty:
            fig = px.pie(soa, values="count", names="response",
                         hole=0.45,
                         color_discrete_map={
                             "Yes": PALETTE[3], "No": PALETTE[0], "Maybe": PALETTE[2]
                         },
                         template=THEME)
            fig.update_traces(
                texttemplate="%{label}<br>%{customdata[0]:.1f}%",
                customdata=soa[["pct"]].values,
            )
            _chart(fig)
            # Percentage breakdown
            for _, row in soa.iterrows():
                st.caption(f"**{row['response']}**: {row['count']} orders ({row['pct']:.1f}%)")
        else:
            st.info("No 'Should Order Again?' data yet.")

    # ── Row 5 charts ──────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💰 Avg Spend by Meal Type")
        avm = avg_spend_by_meal(fdf)
        if not avm.empty:
            _chart(px.bar(avm, x="meal_type", y="amount_paid",
                          labels={"meal_type": "", "amount_paid": "Avg (₹)"},
                          color_discrete_sequence=[PALETTE[5]], template=THEME,
                          text_auto=".0f"))
    with c2:
        st.subheader("🌍 Spending by Cuisine")
        cuis = spending_by_cuisine(fdf)
        if not cuis.empty:
            _chart(px.bar(cuis.head(8), x="amount_paid", y="cuisine_type",
                          orientation="h",
                          labels={"cuisine_type": "", "amount_paid": "Spend (₹)"},
                          color_discrete_sequence=[PALETTE[6]], template=THEME))

    # ── Top 5 expensive ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💸 Top 5 Most Expensive Orders")
    top5 = fdf.nlargest(5, "amount_paid")[
        ["date", "food_item", "restaurant_name", "platform",
         "amount_paid", "excitement_rating"]
    ].copy()
    top5["date"]              = pd.to_datetime(top5["date"]).dt.strftime("%d %b %Y")
    top5["amount_paid"]       = top5["amount_paid"].apply(lambda x: f"₹{x:,.0f}")
    top5["excitement_rating"] = top5["excitement_rating"].apply(
        lambda x: "⭐" * int(x) if pd.notna(x) else "—"
    )
    top5.columns = ["Date", "Food", "Restaurant", "Platform", "Amount", "Rating"]
    st.dataframe(top5, use_container_width=True, hide_index=True)
