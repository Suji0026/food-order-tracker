# 🍽️ Food Order Tracker v2

Personal food order tracking app — Streamlit + Pandas + Plotly.

---

## 🚀 Quick start

```bash
cd food-order-tracker
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## 📂 File structure

```
food-order-tracker/
├── app.py                    Main entry point & navigation
├── requirements.txt
├── data/
│   └── food_orders.csv       Auto-created on first run
├── utils/
│   ├── file_handler.py       CRUD, import/export, migration
│   ├── analytics.py          KPIs, charts, filters
│   ├── validators.py         Input validation & sanitization
│   ├── helpers.py            Constants, formatters, label builder
│   ├── sample_data.py        Generates 40 sample orders
│   └── migrate.py            One-shot v1→v2 schema upgrade
└── pages/
    ├── dashboard.py          Overview, import/export
    ├── add_order.py          Add new order form
    ├── edit_order.py         Search → select → edit → save
    ├── search_orders.py      Filter, sort, export table
    ├── delete_order.py       Descriptive dropdown + 2-step confirm
    └── analytics_page.py     Dynamic-filter analytics dashboard
```

---

## 🗄️ Schema (v2)

| Field | Type | Notes |
|---|---|---|
| order_id | str | Auto-generated, preserved on edit |
| date | date | |
| time | str HH:MM | |
| day | str | Auto from date |
| weekday_weekend | str | Auto from date |
| meal_type | dropdown | Breakfast/Lunch/Snacks/Dinner |
| food_item | text | Required |
| restaurant_name | text | |
| cuisine_type | dropdown | |
| platform | dropdown | Swiggy/Zomato/… |
| quantity | int | |
| amount_paid | float | Required |
| payment_method | dropdown | |
| excitement_rating | int 1–5 | Was "rating" in v1 |
| should_order_again | dropdown | Yes / No / Maybe |
| repeat_order | dropdown | Yes / No |
| favorite | dropdown | Yes / No |
| city | text | |
| remarks | text | |
| created_at | timestamp | |

**Removed from v1:** delivery_charges, coupon_used, spicy_level, mood, healthy_unhealthy

---

## ✨ What's new in v2

| Feature | Details |
|---|---|
| ✏️ Edit Order | Search → pick descriptive label → pre-filled form → save (ID preserved) |
| 🗑️ Better Delete | `24-May-2026 \| Dinner \| Zomato \| Biryani \| ₹320` labels + 2-step confirm |
| 📊 Analytics filters | Date range, meal, platform, day type, cuisine — all charts update live |
| 🔁 Should Order Again | Yes/No/Maybe field with pie chart + % breakdown |
| 🧹 Removed clutter | Delivery charges, coupon, spicy level, mood, healthy tag gone |
| 🔄 Auto-migration | Old v1 CSVs load transparently — no manual fix needed |

---

## 🔄 Upgrading from v1

Old CSVs work **automatically** — no action needed.

To permanently rewrite the file to v2 schema:

```bash
python utils/migrate.py
```

---

## ☁️ Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → connect repo → set `app.py`
3. Deploy

## 🐳 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t food-tracker . && docker run -p 8501:8501 food-tracker
```
