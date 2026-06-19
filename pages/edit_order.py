"""Edit an existing order — search → select → pre-filled form → save."""
import streamlit as st
import pandas as pd
from datetime import datetime
from datetime import time as dtime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import load_data, update_order
from utils.helpers import (
    MEAL_TYPES, PLATFORMS, CUISINE_TYPES, PAYMENT_METHODS,
    SHOULD_ORDER_AGAIN_OPTIONS, make_order_label,
    get_day_name, get_weekday_weekend, safe_int, safe_float,
)
from utils.validators import validate_order, sanitize_text


def _get_data() -> pd.DataFrame:
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()
    return st.session_state["data"]


def _idx(options: list, value) -> int:
    """Return index of value in list, or 0 if not found."""
    try:
        return options.index(str(value)) if str(value) in options else 0
    except (ValueError, TypeError):
        return 0


def show():
    st.header("✏️ Edit Order")
    st.markdown("---")

    df = _get_data()
    if df.empty:
        st.info("📭 No orders to edit yet. Add some orders first!")
        return

    # ── Step 1 : search ───────────────────────────────────────────────────────
    st.subheader("🔍 Step 1 — Find the order")
    search = st.text_input(
        "Search by food item, platform, restaurant…",
        placeholder="e.g. Biryani, Swiggy, McDonald's"
    )

    filtered = df.copy()
    filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")

    if search.strip():
        q = search.strip().lower()
        mask = (
            filtered["food_item"].str.lower().str.contains(q, na=False)
            | filtered["platform"].str.lower().str.contains(q, na=False)
            | filtered["restaurant_name"].str.lower().str.contains(q, na=False)
            | filtered["cuisine_type"].str.lower().str.contains(q, na=False)
        )
        filtered = filtered[mask]

    if filtered.empty:
        st.warning("No matching orders found.")
        return

    # Sort newest first
    filtered = filtered.sort_values("date", ascending=False)

    # Build label → order_id map
    label_map: dict[str, str] = {}
    for _, row in filtered.iterrows():
        lbl = make_order_label(row)
        # Ensure uniqueness by appending short ID if needed
        if lbl in label_map:
            lbl = f"{lbl}  [{row['order_id']}]"
        label_map[lbl] = str(row["order_id"])

    labels = list(label_map.keys())

    # ── Step 2 : select ───────────────────────────────────────────────────────
    st.subheader("📋 Step 2 — Select order to edit")
    selected_label = st.selectbox(
        "Select order", ["— choose an order —"] + labels, label_visibility="collapsed"
    )

    if selected_label == "— choose an order —":
        st.info("Select an order above to load its details.")
        return

    order_id = label_map[selected_label]
    # Fetch live row (not from potentially stale session df)
    row = df[df["order_id"].astype(str) == order_id]
    if row.empty:
        st.error("Order not found. Try refreshing.")
        return
    o = row.iloc[0]

    # ── Step 3 : edit form ────────────────────────────────────────────────────
    st.subheader(f"📝 Step 3 — Edit details")
    st.caption(f"Order ID: `{order_id}` (preserved on save)")
    st.markdown("---")

    with st.form("edit_order_form"):

        st.subheader("📋 Basic Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            try:
                date_default = pd.to_datetime(o["date"]).date()
            except Exception:
                date_default = pd.Timestamp.now().date()
            order_date = st.date_input("📅 Date *", value=date_default)
        with c2:
            try:
                ts = str(o.get("time", "12:00"))
                hh, mm = map(int, ts.split(":"))
                time_default = dtime(hh, mm)
            except Exception:
                time_default = dtime(12, 0)
            order_time = st.time_input("⏰ Time *", value=time_default)
        with c3:
            meal_type = st.selectbox(
                "🍴 Meal Type *", MEAL_TYPES,
                index=_idx(MEAL_TYPES, o.get("meal_type", ""))
            )

        st.subheader("🥘 Food Details")
        c1, c2 = st.columns(2)
        with c1:
            food_item = st.text_input(
                "🍛 Food Item *", value=str(o.get("food_item", "") or "")
            )
        with c2:
            restaurant_name = st.text_input(
                "🏠 Restaurant Name", value=str(o.get("restaurant_name", "") or "")
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            platform = st.selectbox(
                "📱 Platform *", PLATFORMS,
                index=_idx(PLATFORMS, o.get("platform", ""))
            )
        with c2:
            cui_opts = [""] + CUISINE_TYPES
            cuisine_type = st.selectbox(
                "🌍 Cuisine", cui_opts,
                index=_idx(cui_opts, o.get("cuisine_type", ""))
            )
        with c3:
            qty_val = safe_int(o.get("quantity", 1), default=1)
            qty_val = max(1, min(qty_val, 20))
            quantity = st.number_input("🔢 Quantity", min_value=1, max_value=20, value=qty_val)

        st.subheader("💰 Payment")
        c1, c2 = st.columns(2)
        with c1:
            amount_paid = st.number_input(
                "💵 Amount Paid (₹) *",
                min_value=0.0, step=1.0, format="%.2f",
                value=safe_float(o.get("amount_paid", 0))
            )
        with c2:
            pm_opts = [""] + PAYMENT_METHODS
            payment_method = st.selectbox(
                "💳 Payment Method", pm_opts,
                index=_idx(pm_opts, o.get("payment_method", ""))
            )

        st.subheader("⭐ Experience")
        c1, c2 = st.columns(2)
        with c1:
            r_val = safe_int(o.get("excitement_rating", 3), default=3)
            r_val = r_val if r_val in [1, 2, 3, 4, 5] else 3
            excitement_rating = st.select_slider(
                "🎯 Excitement Rating (1–5)", options=[1, 2, 3, 4, 5], value=r_val
            )
        with c2:
            soa_val = str(o.get("should_order_again", "Yes") or "Yes")
            soa_val = soa_val if soa_val in SHOULD_ORDER_AGAIN_OPTIONS else "Yes"
            should_order_again = st.radio(
                "🔁 Should Order Again?",
                SHOULD_ORDER_AGAIN_OPTIONS,
                index=SHOULD_ORDER_AGAIN_OPTIONS.index(soa_val),
                horizontal=True,
            )

        st.subheader("📌 Additional Info")
        c1, c2, c3 = st.columns(3)
        with c1:
            ro_opts = ["No", "Yes"]
            repeat_order = st.selectbox(
                "📦 Repeat Order?", ro_opts,
                index=_idx(ro_opts, o.get("repeat_order", "No"))
            )
        with c2:
            fav_opts = ["No", "Yes"]
            favorite = st.selectbox(
                "❤️ Favourite?", fav_opts,
                index=_idx(fav_opts, o.get("favorite", "No"))
            )
        with c3:
            city = st.text_input("📍 City", value=str(o.get("city", "") or ""))

        remarks = st.text_area(
            "📝 Remarks", value=str(o.get("remarks", "") or ""), height=80
        )

        save_btn = st.form_submit_button(
            "💾 Save Changes", use_container_width=True, type="primary"
        )

    if save_btn:
        updated = {
            "date":               order_date.strftime("%Y-%m-%d"),
            "time":               order_time.strftime("%H:%M"),
            "day":                get_day_name(order_date),
            "weekday_weekend":    get_weekday_weekend(order_date),
            "meal_type":          meal_type,
            "food_item":          sanitize_text(food_item),
            "restaurant_name":    sanitize_text(restaurant_name),
            "cuisine_type":       cuisine_type,
            "platform":           platform,
            "quantity":           quantity,
            "amount_paid":        amount_paid,
            "payment_method":     payment_method,
            "excitement_rating":  excitement_rating,
            "should_order_again": should_order_again,
            "repeat_order":       repeat_order,
            "favorite":           favorite,
            "city":               sanitize_text(city),
            "remarks":            sanitize_text(remarks),
        }

        # Validate with mandatory fields intact
        check = {**updated, "order_id": order_id}
        is_valid, errors = validate_order(check)
        if not is_valid:
            st.error("⚠️ Fix these errors before saving:")
            for err in errors:
                st.warning(f"• {err}")
        else:
            if update_order(order_id, updated):
                st.success(
                    f"✅ Order updated! **{food_item}** — "
                    f"{order_date.strftime('%d %b %Y')}"
                )
                st.session_state.pop("data", None)
            else:
                st.error("❌ Update failed. Please try again.")
