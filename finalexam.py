import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from functools import reduce

# ------------------------------
# 1. Generate sample data (if files not exist)
# ------------------------------
@st.cache_data
def load_sales_data():
    try:
        sales_df = pd.read_csv("sales_data.csv", parse_dates=["sale_date"])
    except FileNotFoundError:
        np.random.seed(42)
        products = ["Wireless Mouse", "Mechanical Keyboard", "USB-C Cable", "27-inch Monitor", "Laptop Stand",
                    "Noise Cancelling Headphones", "Smart Watch", "Portable Charger", "Webcam", "SSD"]
        categories = ["Electronics", "Accessories", "Monitors", "Audio", "Storage"]
        prod_category = {p: np.random.choice(categories) for p in products}
        dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(90)]
        data = []
        for _ in range(150):
            product = np.random.choice(products)
            quantity = np.random.randint(1, 20)
            unit_price = np.random.choice([29.9, 89.9, 199, 499, 1299])
            sale_date = np.random.choice(dates)
            data.append({
                "product_name": product,
                "category": prod_category[product],
                "quantity": quantity,
                "unit_price": unit_price,
                "sale_date": sale_date
            })
        sales_df = pd.DataFrame(data)
        sales_df["total_sales"] = sales_df["quantity"] * sales_df["unit_price"]
        sales_df.to_csv("sales_data.csv", index=False)
    return sales_df

@st.cache_data
def load_inventory_data():
    try:
        inventory_df = pd.read_csv("inventory_data.csv")
    except FileNotFoundError:
        products = ["Wireless Mouse", "Mechanical Keyboard", "USB-C Cable", "27-inch Monitor", "Laptop Stand",
                    "Noise Cancelling Headphones", "Smart Watch", "Portable Charger", "Webcam", "SSD"]
        categories = ["Electronics", "Accessories", "Monitors", "Audio", "Storage"]
        prod_category = {p: np.random.choice(categories) for p in products}
        stock_levels = np.random.randint(0, 100, size=len(products))
        inventory_df = pd.DataFrame({
            "product_name": products,
            "category": [prod_category[p] for p in products],
            "stock_quantity": stock_levels
        })
        inventory_df.to_csv("inventory_data.csv", index=False)
    return inventory_df

# ------------------------------
# 2. Page configuration
# ------------------------------
st.set_page_config(page_title="ShopEasy Sales & Inventory Dashboard", layout="wide")
st.title(" ShopEasy Sdn Bhd Sales Analytics & Inventory Management Dashboard")

sales_df = load_sales_data()
inventory_df = load_inventory_data()

# ------------------------------
# 3. Sidebar filters (sales data)
# ------------------------------
st.sidebar.header(" Sales Data Filters")
all_categories = sales_df["category"].unique()
selected_categories = st.sidebar.multiselect(
    "Select product categories", all_categories, default=all_categories
)

min_date = sales_df["sale_date"].min()
max_date = sales_df["sale_date"].max()
date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered_sales = sales_df[
    (sales_df["category"].isin(selected_categories)) &
    (sales_df["sale_date"] >= pd.Timestamp(start_date)) &
    (sales_df["sale_date"] <= pd.Timestamp(end_date))
]

# ------------------------------
# 4. Key metrics cards
# ------------------------------
col1, col2, col3 = st.columns(3)
total_revenue = filtered_sales["total_sales"].sum()
total_quantity = filtered_sales["quantity"].sum()
avg_price = filtered_sales["unit_price"].mean() if len(filtered_sales) > 0 else 0

col1.metric(" Total Revenue (RM)", f"{total_revenue:,.2f}")
col2.metric(" Total Quantity Sold", f"{total_quantity:,}")
col3.metric(" Average Unit Price (RM)", f"{avg_price:.2f}")

# ------------------------------
# 5. Dynamic data table
# ------------------------------
st.subheader(" Filtered Sales Details")
st.dataframe(filtered_sales, use_container_width=True)

# ------------------------------
# 6. Visualization part (b)
# ------------------------------
st.header(" Sales Visualization Analysis")

# 6.1 Bar chart using Seaborn: total revenue by category
col_ch1, col_ch2 = st.columns(2)
with col_ch1:
    st.subheader("Total Revenue by Category (Seaborn)")
    cat_revenue_df = filtered_sales.groupby("category")["total_sales"].sum().reset_index()
    fig1, ax1 = plt.subplots()
    sns.barplot(data=cat_revenue_df, x="category", y="total_sales", ax=ax1, palette="Blues_d")
    ax1.set_xlabel("Category")
    ax1.set_ylabel("Total Revenue (RM)")
    ax1.set_title("Total Revenue per Category")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

# 6.2 Time series chart (monthly) with Matplotlib
with col_ch2:
    st.subheader("Monthly Sales Trend")
    filtered_sales["month"] = filtered_sales["sale_date"].dt.to_period("M").astype(str)
    monthly_sales = filtered_sales.groupby("month")["total_sales"].sum()
    fig2, ax2 = plt.subplots()
    ax2.plot(monthly_sales.index, monthly_sales.values, marker="o", linestyle="-", color="green")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Total Sales (RM)")
    ax2.set_title("Monthly Sales Trend")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# 6.3 Custom chart: pie chart (quantity share by category)
st.subheader("Sales Quantity Share by Category (Pie Chart)")
cat_qty = filtered_sales.groupby("category")["quantity"].sum()
fig3, ax3 = plt.subplots()
ax3.pie(cat_qty, labels=cat_qty.index, autopct="%1.1f%%", startangle=90)
ax3.axis("equal")
st.pyplot(fig3)

# ------------------------------
# 7. Inventory management module (c)
# ------------------------------
st.header(" Inventory Management Module")

st.sidebar.header(" Inventory Management Filters")
threshold = st.sidebar.slider("Set stock alert threshold (units)", min_value=0, max_value=100, value=20, step=5)

inv_categories = inventory_df["category"].unique()
selected_inv_cats = st.sidebar.multiselect(
    "Filter inventory by category", inv_categories, default=inv_categories
)

filtered_inventory = inventory_df[inventory_df["category"].isin(selected_inv_cats)]

# Functional programming: filter, map, reduce
inventory_records = filtered_inventory.to_dict("records")
low_stock_records = list(filter(lambda item: item["stock_quantity"] < threshold, inventory_records))
low_stock_info = list(map(lambda item: (item["product_name"], item["stock_quantity"]), low_stock_records))
total_risk_units = reduce(lambda acc, item: acc + item["stock_quantity"], low_stock_records, 0) if low_stock_records else 0

if low_stock_records:
    st.warning(f" {len(low_stock_records)} product(s) have stock below the threshold of {threshold} units! Total units at risk: {total_risk_units}.")
    st.subheader(" Low Stock Products")
    low_df = pd.DataFrame(low_stock_records)
    st.dataframe(low_df, use_container_width=True)
else:
    st.success(f" All products have stock equal or above the threshold ({threshold} units).")

st.subheader(" Complete Inventory Status (Low stock highlighted in red)")

def highlight_low_stock(row):
    if row["stock_quantity"] < threshold:
        return ["background-color: #ffcccc"] * len(row) 
    else:
        return [""] * len(row)

styled_inventory = filtered_inventory.style.apply(highlight_low_stock, axis=1)

st.dataframe(styled_inventory, use_container_width=True)

st.subheader("Stock Quantity Distribution")
fig4, ax4 = plt.subplots()
ax4.hist(filtered_inventory["stock_quantity"], bins=15, color="orange", edgecolor="black")
ax4.set_xlabel("Stock Quantity")
ax4.set_ylabel("Number of Products")
st.pyplot(fig4)
