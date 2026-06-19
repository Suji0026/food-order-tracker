import streamlit as st
from datetime import date, datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    MEAL_TYPES, PLATFORMS, CUISINE_TYPES, PAYMENT_METHODS,
    SHOULD_ORDER_AGAIN_OPTIONS, generate_order_id,
    get_day_name, get_weekday_weekend,
)
from utils.validators import validate_order, sanitize_text
from utils.file_handler import append_order


def show():
    st.header("➕ Add New Order")
    st.markdown("---")

    with st.form("add_order_form", clear_on_submit=True):

        # ── Basic details ────────────────────────────────────────────────────
        st.subheader("📋 Basic Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            order_date = st.date_input("📅 Date *", value=date.today())
        with c2:
            order_time = st.time_input("⏰ Time *", value=datetime.now().time())
        with c3:
            meal_type = st.selectbox("🍴 Meal Type *", MEAL_TYPES)

        # ── Food details ─────────────────────────────────────────────────────
        st.subheader("🥘 Food Details")
        c1, c2 = st.columns(2)
        with c1:
            food_item = st.text_input("🍛 Food Item *", placeholder="e.g. Butter Chicken")
        with c2:
            restaurant_name = st.text_input("🏠 Restaurant Name", placeholder="e.g. Behrouz Biryani")

        c1, c2, c3 = st.columns(3)
        with c1:
            platform = st.selectbox("📱 Platform *", PLATFORMS)
        with c2:
            cuisine_type = st.selectbox("🌍 Cuisine Type", [""] + CUISINE_TYPES)
        with c3:
            quantity = st.number_input("🔢 Quantity", min_value=1, max_value=20, value=1)

        # ── Payment ──────────────────────────────────────────────────────────
        st.subheader("💰 Payment")
        c1, c2 = st.columns(2)
        with c1:
            amount_paid = st.number_input(
                "💵 Amount Paid (₹) *", min_value=0.0, step=1.0, format="%.2f"
            )
        with c2:
            payment_method = st.selectbox("💳 Payment Method", [""] + PAYMENT_METHODS)

        # ── Experience ───────────────────────────────────────────────────────
        st.subheader("⭐ Experience")
        c1, c2 = st.columns(2)
        with c1:
            excitement_rating = st.select_slider(
                "🎯 Excitement Rating (1–5)", options=[1, 2, 3, 4, 5], value=4,
                help="1 = Disappointing · 5 = Amazing"
            )
        with c2:
            should_order_again = st.radio(
                "🔁 Should Order Again?",
                SHOULD_ORDER_AGAIN_OPTIONS,
                horizontal=True,
            )

        # ── Additional info ──────────────────────────────────────────────────
        st.subheader("📌 Additional Info")
        c1, c2, c3 = st.columns(3)
        with c1:
            repeat_order = st.selectbox("📦 Repeat Order?", ["No", "Yes"])
        with c2:
            favorite = st.selectbox("❤️ Favourite?", ["No", "Yes"])
        with c3:
            city = st.text_input("📍 City", value="Mumbai")

        remarks = st.text_area("📝 Remarks", placeholder="Any notes...", height=80)

        submitted = st.form_submit_button(
            "✅ Save Order", use_container_width=True, type="primary"
        )

    if submitted:
        order = {
            "order_id":           generate_order_id(),
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
            "created_at":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        is_valid, errors = validate_order(order)
        if not is_valid:
            st.error("⚠️ Please fix these errors before saving:")
            for err in errors:
                st.warning(f"• {err}")
        else:
            if append_order(order):
                day_name = get_day_name(order_date)
                we = get_weekday_weekend(order_date)
                st.success(
                    f"✅ Saved! **{food_item}** on "
                    f"**{order_date.strftime('%d %b %Y')}** ({day_name}, {we})"
                )
                st.balloons()
                st.session_state.pop("data", None)
            else:
                st.error("❌ Failed to save. Please try again.")
