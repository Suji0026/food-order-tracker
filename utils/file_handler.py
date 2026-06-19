import pandas as pd
import os
import shutil
from datetime import datetime

DATA_FILE = "data/food_orders.csv"

# ── Current schema ────────────────────────────────────────────────────────────
COLUMNS = [
    "order_id", "date", "time", "day", "weekday_weekend", "meal_type",
    "food_item", "restaurant_name", "cuisine_type", "platform",
    "quantity", "amount_paid", "payment_method",
    "excitement_rating", "should_order_again",
    "repeat_order", "favorite", "city", "remarks", "created_at",
]

# ── Legacy migration ───────────────────────────────────────────────────────────
# Columns that existed in v1 and must be renamed
LEGACY_RENAMES = {"rating": "excitement_rating"}

# Columns that existed in v1 and must be dropped
LEGACY_DROP = [
    "delivery_charges", "coupon_used", "spicy_level", "mood", "healthy_unhealthy",
]

NUMERIC_COLS = ["amount_paid", "excitement_rating", "quantity"]


def _migrate(df: pd.DataFrame) -> pd.DataFrame:
    """Apply in-memory migration: rename legacy cols, drop removed cols."""
    df = df.rename(columns=LEGACY_RENAMES)
    for col in LEGACY_DROP:
        if col in df.columns:
            df = df.drop(columns=[col])
    # Ensure every current column exists
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS]


def load_data() -> pd.DataFrame:
    """Load CSV, auto-create if missing, apply migration transparently."""
    if not os.path.exists(DATA_FILE):
        os.makedirs("data", exist_ok=True)
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(DATA_FILE, index=False)
        return df
    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
        df = _migrate(df)
        for col in NUMERIC_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
    except Exception as e:
        print(f"[file_handler] load_data error: {e}")
        return pd.DataFrame(columns=COLUMNS)


def save_data(df: pd.DataFrame) -> bool:
    """Atomically save dataframe; keep last 5 rolling backups."""
    try:
        os.makedirs("data", exist_ok=True)
        if os.path.exists(DATA_FILE):
            backup = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            shutil.copy2(DATA_FILE, backup)
            backups = sorted(
                f for f in os.listdir("data") if f.startswith("backup_")
            )
            for old in backups[:-5]:
                try:
                    os.remove(f"data/{old}")
                except OSError:
                    pass
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        tmp = DATA_FILE + ".tmp"
        out.to_csv(tmp, index=False)
        os.replace(tmp, DATA_FILE)
        return True
    except Exception as e:
        print(f"[file_handler] save_data error: {e}")
        return False


def append_order(order: dict) -> bool:
    """Append one order dict; returns success flag."""
    try:
        df = load_data()
        new_row = pd.DataFrame([order])
        df = pd.concat([df, new_row], ignore_index=True)
        return save_data(df)
    except Exception as e:
        print(f"[file_handler] append_order error: {e}")
        return False


def update_order(order_id: str, updated: dict) -> bool:
    """Update fields of an existing order by order_id."""
    try:
        df = load_data()
        idx = df.index[df["order_id"].astype(str) == str(order_id)]
        if len(idx) == 0:
            return False
        for key, val in updated.items():
            df.at[idx[0], key] = val
        return save_data(df)
    except Exception as e:
        print(f"[file_handler] update_order error: {e}")
        return False


def delete_order(order_id: str) -> bool:
    """Remove a single record by order_id."""
    try:
        df = load_data()
        before = len(df)
        df = df[df["order_id"].astype(str) != str(order_id)]
        if len(df) == before:
            return False          # nothing matched
        return save_data(df)
    except Exception as e:
        print(f"[file_handler] delete_order error: {e}")
        return False


def get_order_by_id(order_id: str) -> dict | None:
    """Return a single order as a dict, or None if not found."""
    df = load_data()
    rows = df[df["order_id"].astype(str) == str(order_id)]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


# ── Export / Import ────────────────────────────────────────────────────────────

def export_csv(df: pd.DataFrame) -> bytes:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False).encode("utf-8")


def export_excel(df: pd.DataFrame) -> bytes:
    import io
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="Food Orders")
    return buf.getvalue()


def import_csv(uploaded_file) -> tuple[bool, str, int]:
    """Merge an uploaded CSV into the store (dedup by order_id)."""
    try:
        new_df = pd.read_csv(uploaded_file, dtype=str)
        new_df = _migrate(new_df)
        existing = load_data()
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined.drop_duplicates(subset=["order_id"], keep="last", inplace=True)
        save_data(combined)
        return True, "Import successful", len(new_df)
    except Exception as e:
        return False, str(e), 0
