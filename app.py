import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import date
import tempfile
import shutil

# -----------------------
# File Handling (Absolute Path)
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "expenses.json")

def save_data(data):
    """Safely save expenses data to JSON using atomic writes."""
    with tempfile.NamedTemporaryFile("w", delete=False, dir=BASE_DIR) as tmp_file:
        json.dump(data, tmp_file, indent=4)
        temp_name = tmp_file.name
    shutil.move(temp_name, DATA_FILE)

def load_data():
    """Load expenses data safely, handling empty or corrupted JSON gracefully."""
    data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = f.read().strip()
                if raw:  # Non-empty file
                    data = json.loads(raw)
                else:   # Empty file
                    data = []
        except Exception as e:
            st.warning(f"⚠️ JSON file invalid: {e}. Resetting file.")
            data = []
    save_data(data)
    return data


# -----------------------
# Expense Tracker Logic
# -----------------------
def add_expense(amount, category, exp_date):
    data = load_data()
    data.append({
        "amount": amount,
        "category": category,
        "date": str(exp_date)
    })
    save_data(data)

def get_expenses_df():
    data = load_data()
    if len(data) == 0:
        return pd.DataFrame(columns=["date", "category", "amount"])
    return pd.DataFrame(data)

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Budget Tracker", layout="wide")
st.title("💰 Budget Tracker")

# Debug info: show file being used
st.sidebar.write("📂 File path:", DATA_FILE)
if os.path.exists(DATA_FILE):
    st.sidebar.write("📏 File size:", os.path.getsize(DATA_FILE), "bytes")
    try:
        with open(DATA_FILE, "r") as f:
            st.sidebar.text("📄 File contents:\n" + f.read())
    except:
        st.sidebar.write("⚠️ Could not read file.")
else:
    st.sidebar.write("❌ File not found")

menu = ["Add Expense", "View Expenses", "Analytics Dashboard"]
choice = st.sidebar.radio("📌 Navigation", menu)

# -----------------------
# Add Expense Form
# -----------------------
if choice == "Add Expense":
    st.header("➕ Add a New Expense")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            amount = st.number_input("Amount (£)", min_value=0.01, step=0.01)
        
        with col2:
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"])

        with col3:
            exp_date = st.date_input("Date", value=date.today())

        submitted = st.form_submit_button("Add Expense")

        if submitted:
            add_expense(amount, category, exp_date)
            st.success("✅ Expense Added Successfully!")

# -----------------------
# View Expenses
# -----------------------
elif choice == "View Expenses":
    st.header("📋 Expense History")

    df = get_expenses_df()
    if df.empty:
        st.info("No expenses recorded yet!")
    else:
        st.dataframe(df)

# -----------------------
# Analytics Dashboard
# -----------------------
elif choice == "Analytics Dashboard":
    st.header("📊 Analytics Dashboard")

    df = get_expenses_df()
    if df.empty:
        st.info("No expenses available for analysis!")
    else:
        # Ensure Amount is Numeric
        df["amount"] = pd.to_numeric(df["amount"])

        col1, col2 = st.columns(2)

        # Pie Chart by Category
        with col1:
            st.subheader("Spending by Category")
            pie = px.pie(df, names="category", values="amount", title="Expenses by Category")
            st.plotly_chart(pie, use_container_width=True)

        # Line Chart Over Time
        with col2:
            st.subheader("Spending Over Time")
            df_sorted = df.sort_values("date")
            line = px.line(df_sorted, x="date", y="amount", title="Spending Over Time", markers=True)
            st.plotly_chart(line, use_container_width=True)
        
        # Top 3 Spending Categories
        st.subheader("Top 3 Spending Categories")
        category_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False).head(3)
        st.table(
            category_totals.reset_index().rename(columns={"amount": "Total (£)"})
        )
