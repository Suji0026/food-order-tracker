import uuid
from datetime import datetime, date
import pandas as pd


MEAL_TYPES = ["Breakfast", "Lunch", "Snacks", "Dinner"]

PLATFORMS = [
    "Swiggy", "Zomato", "HungerBox", "EatSure", "EatClub",
    "Direct Restaurant", "Other"
]

CUISINE_TYPES = [
    "Indian", "Chinese", "Italian", "Mexican", "Continental",
    "South Indian", "North Indian", "Fast Food", "Mughlai",
    "Thai", "Japanese", "Mediterranean", "Street Food", "Bakery", "Other"
]

PAYMENT_METHODS = [
    "UPI", "Credit Card", "Debit Card", "Cash", "Wallet", "Net Banking", "Other"
]

SHOULD_ORDER_AGAIN_OPTIONS = ["Yes", "No", "Maybe"]

EXCITEMENT_RATINGS = [1, 2, 3, 4, 5]


def generate_order_id() -> str:
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


def get_day_name(d) -> str:
    if isinstance(d, str):
        d = pd.to_datetime(d)
    return d.strftime("%A")


def get_weekday_weekend(d) -> str:
    if isinstance(d, str):
        d = pd.to_datetime(d)
    if hasattr(d, "dayofweek"):
        dow = d.dayofweek
    else:
        dow = d.weekday()
    return "Weekend" if dow >= 5 else "Weekday"


def format_currency(amount: float) -> str:
    if pd.isna(amount):
        return "₹0.00"
    return f"₹{amount:,.2f}"


def format_date(d) -> str:
    if pd.isna(d) or d is None:
        return ""
    return pd.to_datetime(d).strftime("%d %b %Y")


def rating_stars(rating) -> str:
    if pd.isna(rating):
        return "—"
    stars = int(rating)
    return "⭐" * stars + "☆" * (5 - stars)


def make_order_label(row) -> str:
    """Create a human-readable label for an order row."""
    try:
        d = pd.to_datetime(row["date"]).strftime("%d-%b-%Y")
        meal = row.get("meal_type", "") or ""
        platform = row.get("platform", "") or ""
        food = row.get("food_item", "") or ""
        amount = row.get("amount_paid", 0)
        try:
            amt_str = f"₹{float(amount):.0f}"
        except (ValueError, TypeError):
            amt_str = "₹?"
        return f"{d} | {meal} | {platform} | {food} | {amt_str}"
    except Exception:
        return str(row.get("order_id", "Unknown"))


def safe_int(value, default=3) -> int:
    """Safely convert to int, return default on failure."""
    try:
        v = int(float(value))
        return v
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0) -> float:
    """Safely convert to float, return default on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
