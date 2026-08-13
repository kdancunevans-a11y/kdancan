from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Online Sales Analytics Dashboard",
    page_icon=None,
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("Online Sales Data.csv")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Total Revenue"] = pd.to_numeric(data["Total Revenue"], errors="coerce").fillna(0)
    data["Units Sold"] = pd.to_numeric(data["Units Sold"], errors="coerce").fillna(0)
    data = data.dropna(subset=["Date"])
    data["Month"] = data["Date"].dt.to_period("M").astype(str)
    data["Quarter"] = data["Date"].dt.to_period("Q").astype(str)
    return data

if not DATA_FILE.exists():
    st.error("Online Sales Data.csv was not found. Place it in the same folder as app.py.")
    st.stop()

df = load_data(str(DATA_FILE))

st.title("Online Sales Analytics Dashboard")
st.caption("Interactive OLAP-style analysis of the supplied Online Sales Data.csv file")

st.sidebar.header("Filters")
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = pd.Timestamp(min_date), pd.Timestamp(max_date)

categories = st.sidebar.multiselect("Product category", sorted(df["Product Category"].unique()), default=sorted(df["Product Category"].unique()))
regions = st.sidebar.multiselect("Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique()))
payments = st.sidebar.multiselect("Payment method", sorted(df["Payment Method"].unique()), default=sorted(df["Payment Method"].unique()))

filtered = df[
    df["Date"].between(start_date, end_date)
    & df["Product Category"].isin(categories)
    & df["Region"].isin(regions)
    & df["Payment Method"].isin(payments)
].copy()

if filtered.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

# KPI cards
revenue = filtered["Total Revenue"].sum()
units = filtered["Units Sold"].sum()
transactions = filtered["Transaction ID"].nunique()
avg_order_value = revenue / transactions if transactions else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total revenue", f"${revenue:,.2f}")
k2.metric("Units sold", f"{units:,.0f}")
k3.metric("Transactions", f"{transactions:,}")
k4.metric("Average order value", f"${avg_order_value:,.2f}")

st.info("Use the filters to slice the sales cube. The quarterly view is a roll-up, and the daily view drills down from a selected month.")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Category slice", "Monthly to daily drill-down", "Data table"])

with tab1:
    st.subheader("Roll-up: quarterly revenue")
    quarterly = filtered.groupby("Quarter", as_index=True).agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
        Transactions=("Transaction ID", "nunique"),
    )
    st.bar_chart(quarterly[["Revenue", "Units"]])
    st.dataframe(quarterly.style.format({"Revenue": "${:,.2f}", "Units": "{:,.0f}", "Transactions": "{:,.0f}"}), use_container_width=True)

    st.subheader("Monthly revenue trend")
    monthly = filtered.groupby("Month", as_index=True).agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
    )
    st.line_chart(monthly)

with tab2:
    st.subheader("Slice by product category")
    category_summary = filtered.groupby("Product Category", as_index=False).agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
        Transactions=("Transaction ID", "nunique"),
    ).sort_values("Revenue", ascending=False)
    st.bar_chart(category_summary.set_index("Product Category")[["Revenue", "Units"]])
    st.dataframe(category_summary.style.format({"Revenue": "${:,.2f}", "Units": "{:,.0f}", "Transactions": "{:,.0f}"}), use_container_width=True, hide_index=True)

    st.subheader("Top products in the selected slice")
    top_products = filtered.groupby("Product Name", as_index=False).agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
    ).sort_values("Revenue", ascending=False).head(10)
    st.dataframe(top_products.style.format({"Revenue": "${:,.2f}", "Units": "{:,.0f}"}), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Drill down from monthly summary to daily sales")
    month_options = sorted(filtered["Month"].unique().tolist())
    selected_month = st.selectbox("Select month", month_options)
    month_data = filtered[filtered["Month"] == selected_month]
    daily = month_data.groupby("Date", as_index=True).agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
        Transactions=("Transaction ID", "nunique"),
    )
    st.line_chart(daily[["Revenue", "Units"]])
    st.dataframe(daily.style.format({"Revenue": "${:,.2f}", "Units": "{:,.0f}", "Transactions": "{:,.0f}"}), use_container_width=True)

with tab4:
    st.subheader("Filtered transaction records")
    st.dataframe(filtered.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_online_sales.csv",
        mime="text/csv",
    )

st.caption(f"Showing {len(filtered):,} of {len(df):,} transactions from {min_date} to {max_date}.")
