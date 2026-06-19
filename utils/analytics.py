import pandas as pd
import numpy as np


# ── Filter ────────────────────────────────────────────────────────────────────

def filter_data(
    df: pd.DataFrame,
    date_from=None,
    date_to=None,
    meal_types: list | None = None,
    platforms: list | None = None,
    day_type: str = "All",
    cuisines: list | None = None,
) -> pd.DataFrame:
    """Apply all analytics filters and return a filtered copy."""
    if df.empty:
        return df
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")

    if date_from:
        d = d[d["date"] >= pd.Timestamp(date_from)]
    if date_to:
        d = d[d["date"] <= pd.Timestamp(date_to)]
    if meal_types:
        d = d[d["meal_type"].isin(meal_types)]
    if platforms:
        d = d[d["platform"].isin(platforms)]
    if day_type and day_type != "All":
        d = d[d["weekday_weekend"] == day_type]
    if cuisines:
        d = d[d["cuisine_type"].isin(cuisines)]
    return d


# ── KPIs ──────────────────────────────────────────────────────────────────────

def get_kpis(df: pd.DataFrame) -> dict:
    empty = {
        "total_spent": 0, "total_orders": 0, "avg_order": 0,
        "avg_rating": 0, "top_platform": "—", "top_food": "—",
        "this_month": 0, "weekend_spend": 0, "reorder_pct": 0,
    }
    if df.empty:
        return empty

    total = df["amount_paid"].sum()
    avg   = df["amount_paid"].mean()
    avg_rating = df["excitement_rating"].mean() if df["excitement_rating"].notna().any() else 0
    top_platform = (
        df["platform"].value_counts().idxmax()
        if df["platform"].notna().any() else "—"
    )
    top_food = (
        df["food_item"].value_counts().idxmax()
        if df["food_item"].notna().any() else "—"
    )

    now = pd.Timestamp.now()
    month_mask = (
        pd.to_datetime(df["date"]).dt.month == now.month
    ) & (
        pd.to_datetime(df["date"]).dt.year == now.year
    )
    this_month = df.loc[month_mask, "amount_paid"].sum()

    weekend_mask = df["weekday_weekend"] == "Weekend"
    weekend_spend = df.loc[weekend_mask, "amount_paid"].sum()

    soa = df[
        df["should_order_again"].notna() & (df["should_order_again"] != "")
    ]
    reorder_pct = (
        (soa["should_order_again"] == "Yes").sum() / len(soa) * 100
        if not soa.empty else 0
    )

    return {
        "total_spent":    total,
        "total_orders":   len(df),
        "avg_order":      avg,
        "avg_rating":     avg_rating,
        "top_platform":   top_platform,
        "top_food":       top_food,
        "this_month":     this_month,
        "weekend_spend":  weekend_spend,
        "reorder_pct":    reorder_pct,
    }


# ── Chart data ────────────────────────────────────────────────────────────────

def spending_by_month(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "amount_paid"])
    d = df.copy()
    d["date"]  = pd.to_datetime(d["date"])
    d["month"] = d["date"].dt.to_period("M").astype(str)
    return (
        d.groupby("month")["amount_paid"]
         .sum().reset_index().sort_values("month")
    )


def spending_by_platform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["platform", "amount_paid"])
    return (
        df.groupby("platform")["amount_paid"]
          .sum().reset_index().sort_values("amount_paid", ascending=False)
    )


def meal_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["meal_type", "count"])
    return df["meal_type"].value_counts().reset_index()


def weekday_vs_weekend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby("weekday_weekend")["amount_paid"]
          .agg(total="sum", avg="mean", count="count")
          .reset_index()
    )


def top_food_items(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["food_item", "count"])
    return df["food_item"].value_counts().head(n).reset_index()


def rating_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["excitement_rating", "count"])
    d = df[df["excitement_rating"].notna()].copy()
    d["excitement_rating"] = d["excitement_rating"].astype(int).astype(str)
    return (
        d["excitement_rating"].value_counts()
          .sort_index().reset_index()
          .rename(columns={"excitement_rating": "rating"})
    )


def spending_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["dow"]  = d["date"].dt.day_name()
    order     = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    result    = (
        d.groupby("dow")["amount_paid"]
         .sum().reindex(order).reset_index()
    )
    result.columns = ["day", "amount_paid"]
    return result


def avg_spend_by_meal(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return df.groupby("meal_type")["amount_paid"].mean().reset_index()


def should_order_again_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    d = df[
        df["should_order_again"].notna() & (df["should_order_again"] != "")
    ]
    if d.empty:
        return pd.DataFrame()
    counts = d["should_order_again"].value_counts().reset_index()
    counts.columns = ["response", "count"]
    total = counts["count"].sum()
    counts["pct"] = (counts["count"] / total * 100).round(1)
    return counts


def spending_by_cuisine(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    d = df[df["cuisine_type"].notna() & (df["cuisine_type"] != "")]
    if d.empty:
        return pd.DataFrame()
    return (
        d.groupby("cuisine_type")["amount_paid"]
         .sum().reset_index().sort_values("amount_paid", ascending=False)
    )
