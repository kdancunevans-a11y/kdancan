from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Online Sales Analytics Dashboard", layout="wide")

st.title("Online Sales Analytics Dashboard")
st.caption("Interactive analysis of online sales transactions")


def prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    required = {
        "Date",
        "Product Category",
        "Product Name",
        "Units Sold",
        "Total Revenue",
        "Region",
        "Payment Method",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))

    data = data.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Units Sold"] = pd.to_numeric(data["Units Sold"], errors="coerce")
    data["Total Revenue"] = pd.to_numeric(data["Total Revenue"], errors="coerce")
    data = data.dropna(subset=["Date", "Units Sold", "Total Revenue"])
    data["Month"] = data["Date"].dt.to_period("M").astype(str)
    data["Quarter"] = data["Date"].dt.to_period("Q").astype(str)
    return data


@st.cache_data(show_spinner=False)
def load_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    return prepare_data(pd.read_csv(BytesIO(file_bytes)))


# Look for the CSV in the same folder as app.py. This is the normal deployment setup.
file_candidates = [
    Path(__file__).parent / "Online Sales Data.csv",
    Path(__file__).parent / "online_sales_data.csv",
    Path.cwd() / "Online Sales Data.csv",
]
local_file = next((path for path in file_candidates if path.exists()), None)

if local_file is not None:
    try:
        df = load_csv_bytes(local_file.read_bytes())
        st.sidebar.success(f"Loaded: {local_file.name}")
    except Exception as exc:
        st.error(f"The CSV could not be read: {exc}")
        st.stop()
else:
    st.warning("Online Sales Data.csv is not in the app folder. Upload it below.")
    uploaded_file = st.file_uploader("Upload Online Sales Data.csv", type=["csv"])
    if uploaded_file is None:
        st.info("Add Online Sales Data.csv to the GitHub repository, or upload it here to continue.")
        st.stop()
    try:
        df = load_csv_bytes(uploaded_file.getvalue())
    except Exception as exc:
        st.error(f"The uploaded CSV could not be read: {exc}")
        st.stop()

if df.empty:
    st.error("The dataset contains no valid records after cleaning.")
    st.stop()

st.sidebar.header("Filters")
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])
else:
    start_date = pd.Timestamp(min_date)
    end_date = pd.Timestamp(max_date)

all_categories = sorted(df["Product Category"].dropna().unique().tolist())
all_regions = sorted(df["Region"].dropna().unique().tolist())
all_payments = sorted(df["Payment Method"].dropna().unique().tolist())

categories = st.sidebar.multiselect("Product category", all_categories, default=all_categories)
regions = st.sidebar.multiselect("Region", all_regions, default=all_regions)
payments = st.sidebar.multiselect("Payment method", all_payments, default=all_payments)

filtered = df[
    df["Date"].between(start_date, end_date)
    & df["Product Category"].isin(categories)
    & df["Region"].isin(regions)
    & df["Payment Method"].isin(payments)
].copy()

if filtered.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

revenue = filtered["Total Revenue"].sum()
units = filtered["Units Sold"].sum()
transactions = filtered["Transaction ID"].nunique() if "Transaction ID" in filtered.columns else len(filtered)
avg_order_value = revenue / transactions if transactions else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total revenue", f"${revenue:,.2f}")
k2.metric("Units sold", f"{units:,.0f}")
k3.metric("Transactions", f"{transactions:,}")
k4.metric("Average order value", f"${avg_order_value:,.2f}")

st.info("Use the filters to slice the data. The quarterly view is a roll-up, and the daily view drills down from a selected month.")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Category slice", "Monthly to daily", "Data table"])

with tab1:
    st.subheader("Roll-up: quarterly revenue")
    quarterly = filtered.groupby("Quarter").agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
        Transactions=("Transaction ID", "nunique") if "Transaction ID" in filtered.columns else ("Date", "count"),
    )
    st.bar_chart(quarterly[["Revenue", "Units"]])
    st.dataframe(quarterly.round(2), use_container_width=True)

    st.subheader("Monthly revenue trend")
    monthly = filtered.groupby("Month").agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
    )
    st.line_chart(monthly)

with tab2:
    st.subheader("Slice by product category")
    category_summary = filtered.groupby("Product Category").agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
        Transactions=("Transaction ID", "nunique") if "Transaction ID" in filtered.columns else ("Date", "count"),
    ).sort_values("Revenue", ascending=False)
    st.bar_chart(category_summary[["Revenue", "Units"]])
    st.dataframe(category_summary.round(2), use_container_width=True)

    st.subheader("Top products by revenue")
    top_products = filtered.groupby("Product Name").agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
    ).sort_values("Revenue", ascending=False).head(10)
    st.dataframe(top_products.round(2), use_container_width=True)

with tab3:
    st.subheader("Drill down from monthly summary to daily sales")
    month_options = sorted(filtered["Month"].unique().tolist())
    selected_month = st.selectbox("Select month", month_options)
    month_data = filtered[filtered["Month"] == selected_month]
    daily = month_data.groupby("Date").agg(
        Revenue=("Total Revenue", "sum"),
        Units=("Units Sold", "sum"),
        Transactions=("Transaction ID", "nunique") if "Transaction ID" in month_data.columns else ("Date", "count"),
    )
    st.line_chart(daily[["Revenue", "Units"]])
    st.dataframe(daily.round(2), use_container_width=True)

with tab4:
    st.subheader("Filtered transaction records")
    st.dataframe(filtered.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        "filtered_online_sales.csv",
        "text/csv",
    )

st.caption(f"Showing {len(filtered):,} of {len(df):,} records.")
