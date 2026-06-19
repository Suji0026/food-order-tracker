"""
Migration utility — v1 → v2 schema upgrade.

Run once to permanently update your food_orders.csv to the new schema:
    python utils/migrate.py
"""
import pandas as pd
import shutil
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_FILE = "data/food_orders.csv"

RENAME = {"rating": "excitement_rating"}
DROP   = ["delivery_charges", "coupon_used", "spicy_level", "mood", "healthy_unhealthy"]

NEW_COLUMNS = [
    "order_id", "date", "time", "day", "weekday_weekend", "meal_type",
    "food_item", "restaurant_name", "cuisine_type", "platform",
    "quantity", "amount_paid", "payment_method",
    "excitement_rating", "should_order_again",
    "repeat_order", "favorite", "city", "remarks", "created_at",
]


def migrate():
    if not os.path.exists(DATA_FILE):
        print("No data file found — nothing to migrate.")
        return

    df = pd.read_csv(DATA_FILE, dtype=str)
    original_cols = list(df.columns)
    original_rows = len(df)

    # Backup
    backup = f"data/pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy2(DATA_FILE, backup)
    print(f"✅ Backup saved → {backup}")

    # Rename
    df = df.rename(columns=RENAME)
    renamed = [k for k in RENAME if k in original_cols]
    if renamed:
        print(f"  Renamed columns: {renamed}")

    # Drop
    dropped = [c for c in DROP if c in df.columns]
    df = df.drop(columns=dropped, errors="ignore")
    if dropped:
        print(f"  Dropped columns: {dropped}")

    # Add missing
    for col in NEW_COLUMNS:
        if col not in df.columns:
            df[col] = ""
            print(f"  Added column: {col}")

    df = df[NEW_COLUMNS]
    df.to_csv(DATA_FILE, index=False)

    print(f"\n✅ Migration complete.")
    print(f"   Rows preserved : {original_rows}")
    print(f"   New schema     : {NEW_COLUMNS}")


if __name__ == "__main__":
    migrate()
