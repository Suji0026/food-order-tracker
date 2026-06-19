"""Generate fresh sample data using the current schema."""
import pandas as pd
import random
from datetime import datetime, timedelta
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import (
    get_day_name, get_weekday_weekend, generate_order_id,
    MEAL_TYPES, PLATFORMS, CUISINE_TYPES, PAYMENT_METHODS,
    SHOULD_ORDER_AGAIN_OPTIONS,
)

FOOD_CATALOG = [
    ("Butter Chicken",    "North Indian",  "Swiggy"),
    ("Masala Dosa",       "South Indian",  "Zomato"),
    ("Veg Biryani",       "Indian",        "Swiggy"),
    ("Chicken Biryani",   "Indian",        "Zomato"),
    ("Paneer Tikka",      "North Indian",  "EatSure"),
    ("Margherita Pizza",  "Italian",       "Swiggy"),
    ("Veg Burger",        "Fast Food",     "Zomato"),
    ("Chicken Wrap",      "Fast Food",     "EatClub"),
    ("Hakka Noodles",     "Chinese",       "Swiggy"),
    ("Spring Rolls",      "Chinese",       "Zomato"),
    ("Pasta Arrabbiata",  "Italian",       "Direct Restaurant"),
    ("Dal Makhani",       "North Indian",  "HungerBox"),
    ("Rajma Chawal",      "North Indian",  "HungerBox"),
    ("Chole Bhature",     "North Indian",  "Direct Restaurant"),
    ("Pav Bhaji",         "Street Food",   "Swiggy"),
    ("Vada Pav",          "Street Food",   "Direct Restaurant"),
    ("Idli Sambar",       "South Indian",  "Zomato"),
    ("Chicken Tikka",     "North Indian",  "Swiggy"),
    ("Shahi Paneer",      "North Indian",  "EatSure"),
    ("Fried Rice",        "Chinese",       "Zomato"),
    ("Samosa",            "Street Food",   "Direct Restaurant"),
    ("Grilled Sandwich",  "Fast Food",     "EatClub"),
    ("Poha",              "Indian",        "HungerBox"),
    ("Paratha",           "North Indian",  "Direct Restaurant"),
    ("Upma",              "South Indian",  "HungerBox"),
    ("Cold Coffee",       "Bakery",        "Swiggy"),
    ("Momos",             "Street Food",   "Zomato"),
    ("Thali",             "Indian",        "Direct Restaurant"),
    ("Fish Curry",        "Indian",        "Swiggy"),
    ("Paneer Roll",       "North Indian",  "Zomato"),
]

RESTAURANTS = [
    "Behrouz Biryani", "Fassos", "Box8", "Wow Momo", "Burger King",
    "McDonald's", "Domino's", "KFC", "Subway", "Haldiram's",
    "MTR", "Sagar Ratna", "Punjab Grill", "Office Canteen",
    "Dhabba", "Chaayos", "Home Kitchen", "Cafe Coffee Day",
]

MEAL_WINDOW = {
    "Breakfast": (7,   10),
    "Lunch":     (12,  14),
    "Snacks":    (16,  18),
    "Dinner":    (19,  23),
}

REMARKS_POOL = [
    "Delivered on time", "Great packaging", "Food was cold",
    "Loved it!", "Average taste", "Will reorder",
    "Good value for money", "Late delivery", "Fresh food",
    "", "", "", "",
]


def _rand_time(meal: str) -> str:
    sh, eh = MEAL_WINDOW[meal]
    total_mins = (eh - sh) * 60
    m = random.randint(0, total_mins)
    return f"{sh + m // 60:02d}:{m % 60:02d}"


def generate_sample_data(n: int = 40) -> list[dict]:
    orders = []
    base = datetime.now() - timedelta(days=180)

    for _ in range(n):
        dt     = base + timedelta(days=random.randint(0, 180))
        meal   = random.choice(MEAL_TYPES)
        food, cuisine, platform = random.choice(FOOD_CATALOG)
        amount = round(random.uniform(60, 600), 2)

        orders.append({
            "order_id":          generate_order_id(),
            "date":              dt.strftime("%Y-%m-%d"),
            "time":              _rand_time(meal),
            "day":               get_day_name(dt),
            "weekday_weekend":   get_weekday_weekend(dt),
            "meal_type":         meal,
            "food_item":         food,
            "restaurant_name":   random.choice(RESTAURANTS),
            "cuisine_type":      cuisine,
            "platform":          platform,
            "quantity":          random.choice([1, 1, 1, 2, 2, 3]),
            "amount_paid":       amount,
            "payment_method":    random.choice(PAYMENT_METHODS),
            "excitement_rating": random.randint(2, 5),
            "should_order_again": random.choice(SHOULD_ORDER_AGAIN_OPTIONS),
            "repeat_order":      random.choice(["Yes", "No", "No", "No"]),
            "favorite":          random.choice(["Yes", "No", "No", "No"]),
            "city":              random.choice(["Mumbai", "Mumbai", "Thane", "Navi Mumbai"]),
            "remarks":           random.choice(REMARKS_POOL),
            "created_at":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return orders


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    rows = generate_sample_data(40)
    df = pd.DataFrame(rows)
    df.to_csv("data/food_orders.csv", index=False)
    print(f"Generated {len(df)} sample orders → data/food_orders.csv")
