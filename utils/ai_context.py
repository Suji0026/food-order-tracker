"""
Build a rich, structured context string from the CSV data
that is injected into every AI assistant prompt.

Rules:
- No invented data. Every number comes directly from the DataFrame.
- Keeps the context compact enough to fit in a Claude message.
- Groups / aggregates so the model can reason numerically.
"""
from __future__ import annotations

import json
import textwrap
from datetime import datetime

import pandas as pd


# ── Public entry point ────────────────────────────────────────────────────────

def build_context(df: pd.DataFrame) -> str:
    """
    Return a structured text block describing the entire order history.
    Returns a short 'no data' message if the DataFrame is empty.
    """
    if df.empty:
        return "NO_DATA"

    df = _prep(df)
    sections: list[str] = []

    sections.append(_overview(df))
    sections.append(_platform_stats(df))
    sections.append(_cuisine_stats(df))
    sections.append(_meal_type_stats(df))
    sections.append(_top_food_items(df))
    sections.append(_restaurant_stats(df))
    sections.append(_spending_trends(df))
    sections.append(_reorder_analysis(df))
    sections.append(_recent_orders(df))
    sections.append(_all_orders_compact(df))

    return "\n\n".join(s for s in sections if s)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["date"]              = pd.to_datetime(d["date"], errors="coerce")
    d["amount_paid"]       = pd.to_numeric(d["amount_paid"],       errors="coerce")
    d["excitement_rating"] = pd.to_numeric(d["excitement_rating"], errors="coerce")
    d["quantity"]          = pd.to_numeric(d["quantity"],          errors="coerce").fillna(1)
    # Normalise text fields
    for col in ["food_item","restaurant_name","cuisine_type","platform",
                "meal_type","remarks","should_order_again","weekday_weekend","day"]:
        if col in d.columns:
            d[col] = d[col].fillna("").astype(str).str.strip()
    return d


def _fmt(val) -> str:
    """Format a float for display."""
    try:
        return f"{float(val):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _overview(df: pd.DataFrame) -> str:
    total_orders   = len(df)
    total_spend    = df["amount_paid"].sum()
    avg_spend      = df["amount_paid"].mean()
    avg_rating     = df["excitement_rating"].mean()
    date_min       = df["date"].min()
    date_max       = df["date"].max()
    total_items    = df["quantity"].sum()

    lines = [
        "=== FOOD ORDER DATABASE OVERVIEW ===",
        f"Total orders       : {total_orders}",
        f"Total items ordered: {int(total_items)}",
        f"Total spend        : ₹{_fmt(total_spend)}",
        f"Average per order  : ₹{_fmt(avg_spend)}",
        f"Overall avg rating : {_fmt(avg_rating)} / 5",
        f"Date range         : {date_min.strftime('%d-%b-%Y') if pd.notna(date_min) else 'N/A'}"
                          f" → {date_max.strftime('%d-%b-%Y') if pd.notna(date_max) else 'N/A'}",
    ]
    return "\n".join(lines)


def _platform_stats(df: pd.DataFrame) -> str:
    g = df.groupby("platform").agg(
        orders   =("order_id",          "count"),
        avg_spend=("amount_paid",        "mean"),
        avg_rating=("excitement_rating", "mean"),
        reorders =("should_order_again", lambda x: (x == "Yes").sum()),
    ).sort_values("orders", ascending=False)

    lines = ["=== PLATFORM STATISTICS ==="]
    for platform, row in g.iterrows():
        if not platform:
            continue
        lines.append(
            f"  {platform}: {int(row['orders'])} orders | "
            f"Avg ₹{_fmt(row['avg_spend'])} | "
            f"Avg rating {_fmt(row['avg_rating'])}/5 | "
            f"Would reorder: {int(row['reorders'])} times"
        )
    return "\n".join(lines)


def _cuisine_stats(df: pd.DataFrame) -> str:
    g = df[df["cuisine_type"] != ""].groupby("cuisine_type").agg(
        orders    =("order_id",          "count"),
        total_spend=("amount_paid",       "sum"),
        avg_spend =("amount_paid",        "mean"),
        avg_rating=("excitement_rating",  "mean"),
    ).sort_values("orders", ascending=False)

    lines = ["=== CUISINE STATISTICS ==="]
    for cuisine, row in g.iterrows():
        lines.append(
            f"  {cuisine}: {int(row['orders'])} orders | "
            f"Total ₹{_fmt(row['total_spend'])} | "
            f"Avg ₹{_fmt(row['avg_spend'])} | "
            f"Avg rating {_fmt(row['avg_rating'])}/5"
        )
    return "\n".join(lines)


def _meal_type_stats(df: pd.DataFrame) -> str:
    g = df.groupby("meal_type").agg(
        orders    =("order_id",           "count"),
        avg_spend =("amount_paid",         "mean"),
        avg_rating=("excitement_rating",   "mean"),
    ).sort_values("orders", ascending=False)

    wd = df[df["weekday_weekend"] == "Weekday"].groupby("meal_type")["amount_paid"].sum()
    we = df[df["weekday_weekend"] == "Weekend"].groupby("meal_type")["amount_paid"].sum()

    lines = ["=== MEAL TYPE STATISTICS ==="]
    for meal, row in g.iterrows():
        if not meal:
            continue
        lines.append(
            f"  {meal}: {int(row['orders'])} orders | "
            f"Avg ₹{_fmt(row['avg_spend'])} | "
            f"Avg rating {_fmt(row['avg_rating'])}/5 | "
            f"Weekday spend ₹{_fmt(wd.get(meal, 0))} | "
            f"Weekend spend ₹{_fmt(we.get(meal, 0))}"
        )
    return "\n".join(lines)


def _top_food_items(df: pd.DataFrame, n: int = 20) -> str:
    g = df.groupby("food_item").agg(
        orders         =("order_id",          "count"),
        avg_rating     =("excitement_rating",  "mean"),
        avg_spend      =("amount_paid",        "mean"),
        total_spend    =("amount_paid",        "sum"),
        reorder_yes    =("should_order_again", lambda x: (x == "Yes").sum()),
        reorder_no     =("should_order_again", lambda x: (x == "No").sum()),
        reorder_maybe  =("should_order_again", lambda x: (x == "Maybe").sum()),
        remarks        =("remarks",            lambda x: " | ".join(
                             r for r in x.unique() if r)),
    ).sort_values("orders", ascending=False).head(n)

    lines = ["=== TOP FOOD ITEMS (by order frequency) ==="]
    for item, row in g.iterrows():
        if not item:
            continue
        lines.append(
            f"  [{item}] "
            f"Orders:{int(row['orders'])} | "
            f"Avg rating:{_fmt(row['avg_rating'])}/5 | "
            f"Avg price:₹{_fmt(row['avg_spend'])} | "
            f"Total spend:₹{_fmt(row['total_spend'])} | "
            f"Would reorder→ Yes:{int(row['reorder_yes'])} "
            f"No:{int(row['reorder_no'])} "
            f"Maybe:{int(row['reorder_maybe'])} | "
            f"Remarks: {row['remarks'][:200] if row['remarks'] else 'None'}"
        )
    return "\n".join(lines)


def _restaurant_stats(df: pd.DataFrame, n: int = 15) -> str:
    d = df[df["restaurant_name"] != ""]
    if d.empty:
        return ""
    g = d.groupby("restaurant_name").agg(
        orders       =("order_id",          "count"),
        avg_rating   =("excitement_rating",  "mean"),
        avg_spend    =("amount_paid",        "mean"),
        total_spend  =("amount_paid",        "sum"),
        reorder_yes  =("should_order_again", lambda x: (x == "Yes").sum()),
        cuisines     =("cuisine_type",       lambda x: ", ".join(sorted(set(x) - {""}))),
        remarks      =("remarks",            lambda x: " | ".join(
                           r for r in x.unique() if r)[:300]),
    ).sort_values("avg_rating", ascending=False).head(n)

    lines = ["=== RESTAURANT STATISTICS (sorted by avg rating) ==="]
    for rest, row in g.iterrows():
        lines.append(
            f"  [{rest}] "
            f"Orders:{int(row['orders'])} | "
            f"Avg rating:{_fmt(row['avg_rating'])}/5 | "
            f"Avg spend:₹{_fmt(row['avg_spend'])} | "
            f"Total:₹{_fmt(row['total_spend'])} | "
            f"Would reorder Yes:{int(row['reorder_yes'])} | "
            f"Cuisines:{row['cuisines']} | "
            f"Remarks:{row['remarks'] or 'None'}"
        )
    return "\n".join(lines)


def _spending_trends(df: pd.DataFrame) -> str:
    d = df.copy()
    d["month"] = d["date"].dt.to_period("M").astype(str)
    monthly = d.groupby("month")["amount_paid"].agg(
        total="sum", count="count", avg="mean"
    ).sort_index()

    lines = ["=== MONTHLY SPENDING TREND ==="]
    for month, row in monthly.iterrows():
        lines.append(
            f"  {month}: ₹{_fmt(row['total'])} total | "
            f"{int(row['count'])} orders | "
            f"Avg ₹{_fmt(row['avg'])}/order"
        )

    # Weekday vs weekend
    wdwe = d.groupby("weekday_weekend")["amount_paid"].agg(
        total="sum", count="count", avg="mean"
    )
    lines.append("--- Weekday vs Weekend ---")
    for dtype, row in wdwe.iterrows():
        lines.append(
            f"  {dtype}: ₹{_fmt(row['total'])} total | "
            f"{int(row['count'])} orders | "
            f"Avg ₹{_fmt(row['avg'])}/order"
        )

    # Time of day
    d["hour"] = pd.to_datetime(d["time"], format="%H:%M", errors="coerce").dt.hour
    time_buckets = {
        "Morning (6-11)":  d[d["hour"].between(6,  10)]["amount_paid"].sum(),
        "Afternoon(12-15)":d[d["hour"].between(12, 15)]["amount_paid"].sum(),
        "Evening (16-18)": d[d["hour"].between(16, 18)]["amount_paid"].sum(),
        "Night (19-23)":   d[d["hour"].between(19, 23)]["amount_paid"].sum(),
    }
    lines.append("--- Spending by Time of Day ---")
    for bucket, total in time_buckets.items():
        lines.append(f"  {bucket}: ₹{_fmt(total)}")

    return "\n".join(lines)


def _reorder_analysis(df: pd.DataFrame) -> str:
    soa = df[df["should_order_again"] != ""].copy()
    if soa.empty:
        return ""

    counts = soa["should_order_again"].value_counts()
    total  = len(soa)

    lines = ["=== REORDER (SHOULD ORDER AGAIN) ANALYSIS ==="]
    for val, cnt in counts.items():
        lines.append(f"  {val}: {cnt} ({cnt/total*100:.1f}%)")

    # Top items with Yes
    yes_items = (
        soa[soa["should_order_again"] == "Yes"]
        .groupby("food_item")["order_id"].count()
        .sort_values(ascending=False).head(10)
    )
    lines.append("--- Top items marked 'Would Order Again' ---")
    for item, cnt in yes_items.items():
        lines.append(f"  {item}: {cnt} times")

    # Items marked No
    no_items = (
        soa[soa["should_order_again"] == "No"]
        .groupby("food_item")["order_id"].count()
        .sort_values(ascending=False).head(5)
    )
    lines.append("--- Items marked 'Would NOT Order Again' ---")
    for item, cnt in no_items.items():
        lines.append(f"  {item}: {cnt} times")

    return "\n".join(lines)


def _recent_orders(df: pd.DataFrame, n: int = 10) -> str:
    recent = df.sort_values("date", ascending=False).head(n)
    lines  = [f"=== LAST {n} ORDERS (most recent first) ==="]
    for _, row in recent.iterrows():
        d = row["date"].strftime("%d-%b-%Y") if pd.notna(row["date"]) else "?"
        lines.append(
            f"  {d} | {row['meal_type']} | {row['food_item']} | "
            f"{row['restaurant_name']} | {row['platform']} | "
            f"₹{_fmt(row['amount_paid'])} | "
            f"Rating:{_fmt(row['excitement_rating'])}/5 | "
            f"OrderAgain:{row['should_order_again']} | "
            f"Remarks:{row['remarks'] or '—'}"
        )
    return "\n".join(lines)


def _all_orders_compact(df: pd.DataFrame) -> str:
    """Full order list in a compact one-line-per-order format for deep queries."""
    lines = ["=== FULL ORDER HISTORY (compact) ==="]
    for _, row in df.sort_values("date", ascending=False).iterrows():
        d = row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else "?"
        lines.append(
            f"{d}|{row['meal_type']}|{row['food_item']}|"
            f"{row['restaurant_name']}|{row['platform']}|"
            f"{row['cuisine_type']}|₹{row['amount_paid']}|"
            f"R:{row['excitement_rating']}|{row['should_order_again']}|"
            f"{row['weekday_weekend']}|{row['remarks']}"
        )
    return "\n".join(lines)
