"""Delete an order — descriptive dropdown, two-step confirmation."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import load_data, delete_order
from utils.helpers import make_order_label


def _get_data() -> pd.DataFrame:
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()
    return st.session_state["data"]


def _reset_confirm():
    st.session_state.pop("del_pending_id",    None)
    st.session_state.pop("del_pending_label", None)


def show():
    st.header("🗑️ Delete Order")
    st.markdown("---")

    df = _get_data()
    if df.empty:
        st.info("📭 No orders to delete.")
        return

    # ── Search ────────────────────────────────────────────────────────────────
    search = st.text_input(
        "🔍 Search to narrow the list",
        placeholder="e.g. Biryani, Zomato, Swiggy…"
    )

    filtered = df.copy()
    filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")
    filtered = filtered.sort_values("date", ascending=False)

    if search.strip():
        q = search.strip().lower()
        mask = (
            filtered["food_item"].str.lower().str.contains(q, na=False)
            | filtered["platform"].str.lower().str.contains(q, na=False)
            | filtered["restaurant_name"].str.lower().str.contains(q, na=False)
        )
        filtered = filtered[mask]

    if filtered.empty:
        st.warning("No matching orders found.")
        return

    # ── Descriptive dropdown ─────────────────────────────────────────────────
    label_map: dict[str, str] = {}
    for _, row in filtered.iterrows():
        lbl = make_order_label(row)
        if lbl in label_map:                              # handle rare duplicates
            lbl = f"{lbl}  [{row['order_id']}]"
        label_map[lbl] = str(row["order_id"])

    options = ["— select an order to delete —"] + list(label_map.keys())
    selected_label = st.selectbox("Select order", options, label_visibility="collapsed")

    if selected_label == options[0]:
        st.info("Choose an order from the dropdown above.")
        _reset_confirm()
        return

    order_id = label_map[selected_label]

    # ── Order preview ─────────────────────────────────────────────────────────
    row_data = df[df["order_id"].astype(str) == order_id]
    if not row_data.empty:
        r = row_data.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Food Item",  str(r.get("food_item",   "—")))
        c2.metric("Platform",   str(r.get("platform",    "—")))
        c3.metric("Amount",     f"₹{float(r.get('amount_paid', 0) or 0):,.0f}")
        c4.metric("Excitement", f"{'⭐' * int(float(r.get('excitement_rating', 0) or 0))}")

    st.markdown("---")

    # ── Step 1: initiate delete ───────────────────────────────────────────────
    pending_id = st.session_state.get("del_pending_id")

    if pending_id != order_id:
        # If user changed selection mid-flow, reset confirmation
        _reset_confirm()
        if st.button("🗑️ Delete This Order", type="primary", use_container_width=False):
            st.session_state["del_pending_id"]    = order_id
            st.session_state["del_pending_label"] = selected_label
            st.rerun()

    else:
        # ── Step 2: confirm ───────────────────────────────────────────────────
        st.warning(
            f"⚠️ **Are you sure you want to permanently delete this order?**\n\n"
            f"```\n{selected_label}\n```\n\n"
            f"This action **cannot be undone**."
        )
        col_yes, col_no, _ = st.columns([1, 1, 4])
        with col_yes:
            if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
                if delete_order(order_id):
                    st.session_state.pop("data", None)
                    _reset_confirm()
                    st.success("✅ Order deleted successfully.")
                    st.rerun()
                else:
                    st.error("❌ Deletion failed. Please try again.")
                    _reset_confirm()
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                _reset_confirm()
                st.info("Deletion cancelled.")
                st.rerun()
