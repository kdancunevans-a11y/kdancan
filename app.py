import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="County Healthcare OLAP Dashboard",
    layout="wide",
)

st.title("County Healthcare OLAP Dashboard")
st.caption("Interactive demonstration using reproducible simulated clinic records")

@st.cache_data
def create_data(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    clinics = ["Nairobi CBD", "Mombasa Central", "Kisumu West", "Nakuru North", "Eldoret East"]
    ailments = ["Respiratory", "Gastrointestinal", "Malaria", "Injury", "Other"]
    medicines = {
        "Respiratory": "Antihistamines",
        "Gastrointestinal": "Oral Rehydration",
        "Malaria": "Antimalarials",
        "Injury": "Analgesics",
        "Other": "General Supplies",
    }

    rows = []
    for day in dates:
        month = day.month
        seasonal_weights = {
            "Respiratory": 0.38 if month in [6, 7, 8, 9] else 0.20,
            "Gastrointestinal": 0.30 if month in [1, 2, 3, 10, 11, 12] else 0.16,
            "Malaria": 0.28 if month in [4, 5, 10, 11] else 0.13,
            "Injury": 0.12,
            "Other": 0.11,
        }
        ailments_today = list(seasonal_weights)
        probabilities = np.array(list(seasonal_weights.values()))
        probabilities = probabilities / probabilities.sum()
        for clinic in clinics:
            visits = int(rng.poisson(32 if day.weekday() < 5 else 20))
            for _ in range(visits):
                ailment = rng.choice(ailments_today, p=probabilities)
                attendance = 1
                medicine = medicines[ailment]
                supply = int(max(0, rng.normal(18, 5)))
                rows.append([day, clinic, ailment, medicine, attendance, supply])

    df = pd.DataFrame(
        rows,
        columns=["Date", "Clinic", "Ailment", "Medicine", "Attendance", "SupplyIssued"],
    )
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)
    df["Day"] = df["Date"].dt.day
    return df


df = create_data()

st.sidebar.header("Dashboard controls")
clinic_options = ["All clinics"] + sorted(df["Clinic"].unique().tolist())
ailment_options = ["All ailments"] + sorted(df["Ailment"].unique().tolist())
selected_clinic = st.sidebar.selectbox("Clinic", clinic_options)
selected_ailment = st.sidebar.selectbox("Ailment category", ailment_options)
selected_quarter = st.sidebar.selectbox("Quarter", ["All quarters"] + sorted(df["Quarter"].unique().tolist()))

filtered = df.copy()
if selected_clinic != "All clinics":
    filtered = filtered[filtered["Clinic"] == selected_clinic]
if selected_ailment != "All ailments":
    filtered = filtered[filtered["Ailment"] == selected_ailment]
if selected_quarter != "All quarters":
    filtered = filtered[filtered["Quarter"] == selected_quarter]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

st.info("Use the sidebar to slice the data by clinic, ailment, or quarter. The charts demonstrate OLAP roll-up and drill-down operations.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Clinic visits", f"{filtered['Attendance'].sum():,}")
k2.metric("Supply issued", f"{filtered['SupplyIssued'].sum():,}")
k3.metric("Ailment categories", f"{filtered['Ailment'].nunique()}")
k4.metric("Active clinics", f"{filtered['Clinic'].nunique()}")

st.subheader("Slice: Ailment and medication distribution")
category_summary = (
    filtered.groupby(["Ailment", "Medicine"], as_index=False)
    .agg(Visits=("Attendance", "sum"), SupplyIssued=("SupplyIssued", "sum"))
    .sort_values("Visits", ascending=False)
)
st.dataframe(category_summary, use_container_width=True, hide_index=True)

st.subheader("Roll-up: Quarter-by-quarter clinic attendance")
quarterly = filtered.groupby("Quarter", as_index=False).agg(
    ClinicVisits=("Attendance", "sum"), SupplyIssued=("SupplyIssued", "sum")
)
st.bar_chart(quarterly.set_index("Quarter")[["ClinicVisits", "SupplyIssued"]])

st.subheader("Monthly trend")
monthly = filtered.groupby("Month", as_index=False).agg(
    ClinicVisits=("Attendance", "sum"), SupplyIssued=("SupplyIssued", "sum")
)
st.line_chart(monthly.set_index("Month")[["ClinicVisits", "SupplyIssued"]])

st.subheader("Drill-down: Monthly summary to daily data")
month_options = sorted(filtered["Month"].unique().tolist())
selected_month = st.selectbox("Select a month", month_options)
daily_source = filtered[filtered["Month"] == selected_month]
daily = daily_source.groupby("Date", as_index=False).agg(
    ClinicVisits=("Attendance", "sum"), SupplyIssued=("SupplyIssued", "sum")
)
st.line_chart(daily.set_index("Date")[["ClinicVisits", "SupplyIssued"]])

with st.expander("View filtered records"):
    st.dataframe(filtered.head(500), use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_healthcare_records.csv",
        mime="text/csv",
    )

st.caption("Note: The records are simulated for demonstration. Replace create_data() with a secure data-loading function before production use.")
