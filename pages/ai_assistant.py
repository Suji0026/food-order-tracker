"""
AI Food Order Intelligence Assistant
─────────────────────────────────────
Chat interface backed by Claude (claude-sonnet-4-6).
Data is injected into every request — the model never fabricates.
"""
from __future__ import annotations

import os
import textwrap
import time

import pandas as pd
import streamlit as st

# Project imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.file_handler import load_data
from utils.ai_context   import build_context

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL        = "claude-sonnet-4-6"
MAX_TOKENS   = 1500
HISTORY_LIMIT = 10          # keep last N user+assistant turns in context

SYSTEM_PROMPT = textwrap.dedent("""
You are an AI Food Order Intelligence Assistant integrated into a personal food ordering tracker.

CRITICAL RULES — follow these without exception:
1. Use ONLY the data provided in the <database> block below.
2. NEVER invent, guess, or hallucinate restaurants, ratings, prices, items, or remarks.
3. If the data does not contain enough information to answer, respond with:
   "Insufficient data available in the food tracker database."
4. Always cite EXACT numbers from the data (orders count, avg rating, avg price, reorder count).
5. Explain how every conclusion was derived.

RECOMMENDATION SCORING FORMULA (normalize to 100):
  Score = (40% × avg_rating/5) + (30% × reorder_yes_rate) + (20% × positive_remarks_ratio) + (10% × order_frequency_rate)
  Where:
    - avg_rating/5            → normalized 0–1
    - reorder_yes_rate        → Yes / (Yes + No + Maybe)
    - positive_remarks_ratio  → estimated from remark text (positive sentiment words)
    - order_frequency_rate    → item_orders / max_orders_any_item

RESPONSE FORMAT:
Always structure responses as:
  📊 Summary
  📋 Supporting Data  (bullet points with exact numbers)
  ✅ Recommendation
  💡 Reasoning

For recommendations, rank options and show a score out of 100.

DATABASE (your only source of truth):
<database>
{DATA_CONTEXT}
</database>
""").strip()

STARTER_SUGGESTIONS = [
    "🍛 What's the best biryani I've ordered?",
    "📱 Which platform gives me the best experience?",
    "💸 How much have I spent on Chinese food?",
    "🌙 What do I usually order on weekends?",
    "⭐ Show my top 5 restaurants by rating",
    "🔁 What are my most reordered items?",
    "🍽️ Suggest a dinner under ₹300",
    "📅 What's my monthly spending trend?",
    "😬 Which items should I avoid ordering again?",
    "🍕 Best pizza I've ordered?",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_df() -> pd.DataFrame:
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()
    return st.session_state["data"]


def _get_context(df: pd.DataFrame) -> str:
    ctx_key = "ai_data_context"
    if ctx_key not in st.session_state:
        st.session_state[ctx_key] = build_context(df)
    return st.session_state[ctx_key]


def _call_claude(user_message: str, history: list[dict], context: str) -> str:
    """Call Anthropic API via fetch (runs inside Streamlit Python env)."""
    import json, urllib.request, urllib.error

    system = SYSTEM_PROMPT.replace("{DATA_CONTEXT}", context)

    # Trim history to last HISTORY_LIMIT turns
    trimmed = history[-(HISTORY_LIMIT * 2):]

    payload = {
        "model":      MODEL,
        "max_tokens": MAX_TOKENS,
        "system":     system,
        "messages":   trimmed + [{"role": "user", "content": user_message}],
    }

    # Retrieve API key from Streamlit secrets (local: .streamlit/secrets.toml)
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return (
            "⚠️ **API key not configured.**\n\n"
            "**Local:** add your key to `.streamlit/secrets.toml`\n\n"
            "**Streamlit Cloud:** go to App Settings → Secrets and add:\n"
            "```\nANTHROPIC_API_KEY = \"sk-ant-...\"\n```"
        )

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data    = json.dumps(payload).encode(),
        headers = {
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method = "POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            blocks = data.get("content", [])
            return " ".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body).get("error", {}).get("message", body)
        except Exception:
            err = body
        return f"⚠️ API error ({e.code}): {err}"
    except Exception as e:
        return f"⚠️ Request failed: {e}"


def _render_chat_history(history: list[dict]):
    for msg in history:
        role = msg["role"]
        with st.chat_message("user" if role == "user" else "assistant",
                             avatar="🧑" if role == "user" else "🤖"):
            st.markdown(msg["content"])


def _init_session():
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []
    if "ai_input_key" not in st.session_state:
        st.session_state["ai_input_key"] = 0


# ── Main page ─────────────────────────────────────────────────────────────────

def show():
    _init_session()

    st.header("🤖 AI Food Intelligence Assistant")
    st.caption("Answers are derived exclusively from your order history — no guessing, no hallucination.")
    st.markdown("---")

    df  = _get_df()
    ctx = _get_context(df)

    # ── Empty state ───────────────────────────────────────────────────────────
    if df.empty or ctx == "NO_DATA":
        st.warning(
            "📭 **No order data found.**\n\n"
            "Go to **Dashboard → Load Sample Data** or **Add Order** "
            "to populate your tracker, then return here."
        )
        return

    # ── Sidebar stats ─────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🤖 AI Assistant**")
        st.caption(f"Analysing **{len(df)}** orders")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["ai_messages"] = []
            st.session_state.pop("ai_data_context", None)  # refresh context too
            st.rerun()

    # ── Suggestion chips (only shown when chat is empty) ──────────────────────
    if not st.session_state["ai_messages"]:
        st.subheader("💡 Try asking…")
        cols = st.columns(2)
        for i, suggestion in enumerate(STARTER_SUGGESTIONS):
            if cols[i % 2].button(suggestion, use_container_width=True, key=f"sug_{i}"):
                st.session_state["ai_messages"] = []
                _handle_message(suggestion, df, ctx)
                st.rerun()
        st.markdown("---")

    # ── Chat history ──────────────────────────────────────────────────────────
    _render_chat_history(st.session_state["ai_messages"])

    # ── Input ─────────────────────────────────────────────────────────────────
    prompt = st.chat_input(
        "Ask anything about your food orders…",
        key=f"chat_input_{st.session_state['ai_input_key']}",
    )
    if prompt:
        _handle_message(prompt, df, ctx)
        st.rerun()

    # ── Refresh context note ──────────────────────────────────────────────────
    if st.session_state["ai_messages"]:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh Data Context", use_container_width=True,
                         help="Re-read the CSV so new orders are included in AI answers"):
                st.session_state.pop("ai_data_context", None)
                st.session_state.pop("data",            None)
                st.success("Data context refreshed.")
                st.rerun()


def _handle_message(user_text: str, df: pd.DataFrame, ctx: str):
    """Append user message, call API, append assistant reply."""
    history = st.session_state["ai_messages"]

    # Show user message immediately
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_text)

    history.append({"role": "user", "content": user_text})

    # Stream-style spinner while waiting
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analysing your order history…"):
            reply = _call_claude(user_text, history[:-1], ctx)
        st.markdown(reply)

    history.append({"role": "assistant", "content": reply})
    st.session_state["ai_input_key"] += 1  # reset input widget
