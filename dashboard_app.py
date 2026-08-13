
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Online Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("Online Sales Data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    df['Month_Name'] = df['Date'].dt.strftime('%B %Y')
    df['Day_of_Week'] = df['Date'].dt.day_name()
    df['Week'] = df['Date'].dt.isocalendar().week
    return df

df = load_data()

# Sidebar Filters
st.sidebar.markdown("## 🔧 Filters")

# Date range filter
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Category filter
categories = ['All'] + sorted(df['Product Category'].unique().tolist())
selected_category = st.sidebar.selectbox("Product Category", categories)

# Region filter
regions = ['All'] + sorted(df['Region'].unique().tolist())
selected_region = st.sidebar.selectbox("Region", regions)

# Payment method filter
payment_methods = ['All'] + sorted(df['Payment Method'].unique().tolist())
selected_payment = st.sidebar.selectbox("Payment Method", payment_methods)

# Apply filters
filtered_df = df.copy()
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['Date'].dt.date >= date_range[0]) & 
        (filtered_df['Date'].dt.date <= date_range[1])
    ]
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['Product Category'] == selected_category]
if selected_region != 'All':
    filtered_df = filtered_df[filtered_df['Region'] == selected_region]
if selected_payment != 'All':
    filtered_df = filtered_df[filtered_df['Payment Method'] == selected_payment]

# Title
st.markdown('<div class="main-header">📊 Online Sales Analytics Dashboard</div>', unsafe_allow_html=True)

# Date range info
st.markdown(f"<p style='text-align: center; color: #7f8c8d;'>Data Period: {filtered_df['Date'].min().strftime('%B %d, %Y')} → {filtered_df['Date'].max().strftime('%B %d, %Y')} | {len(filtered_df)} Transactions</p>", unsafe_allow_html=True)

st.markdown("---")

# KPI Cards
st.markdown("### 📈 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_revenue = filtered_df['Total Revenue'].sum()
    st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")

with col2:
    total_units = filtered_df['Units Sold'].sum()
    st.metric("📦 Units Sold", f"{total_units:,}")

with col3:
    avg_order_value = filtered_df['Total Revenue'].mean()
    st.metric("🛒 Avg Order Value", f"${avg_order_value:,.2f}")

with col4:
    total_transactions = len(filtered_df)
    st.metric("🧾 Transactions", f"{total_transactions:,}")

with col5:
    unique_products = filtered_df['Product Name'].nunique()
    st.metric("🏷️ Unique Products", f"{unique_products:,}")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Revenue Trends", 
    "🏷️ Category Analysis", 
    "🌍 Regional Insights", 
    "💳 Payment Methods",
    "📋 Data Explorer"
])

# Tab 1: Revenue Trends
with tab1:
    st.markdown("### Revenue Trends Over Time")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Monthly revenue trend
        monthly_revenue = filtered_df.groupby('Month_Name')['Total Revenue'].sum().reset_index()
        monthly_revenue['Month_Order'] = pd.to_datetime(monthly_revenue['Month_Name'], format='%B %Y')
        monthly_revenue = monthly_revenue.sort_values('Month_Order')

        fig_line = px.line(
            monthly_revenue, 
            x='Month_Name', 
            y='Total Revenue',
            markers=True,
            title='Monthly Revenue Trend',
            labels={'Month_Name': 'Month', 'Total Revenue': 'Revenue ($)'},
            template='plotly_white'
        )
        fig_line.update_traces(line_color='#1f77b4', line_width=3, marker_size=8)
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        # Daily revenue heatmap
        filtered_df['Day'] = filtered_df['Date'].dt.day
        daily_revenue = filtered_df.groupby(['Month_Name', 'Day'])['Total Revenue'].sum().reset_index()
        daily_revenue['Month_Order'] = pd.to_datetime(daily_revenue['Month_Name'], format='%B %Y')
        daily_revenue = daily_revenue.sort_values('Month_Order')

        fig_heatmap = px.density_heatmap(
            daily_revenue,
            x='Day',
            y='Month_Name',
            z='Total Revenue',
            title='Revenue Heatmap (Day vs Month)',
            labels={'Day': 'Day of Month', 'Month_Name': 'Month'},
            color_continuous_scale='Blues'
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # Weekly and daily patterns
    col_w1, col_w2 = st.columns(2)

    with col_w1:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_revenue = filtered_df.groupby('Day_of_Week')['Total Revenue'].sum().reindex(day_order).reset_index()

        fig_dow = px.bar(
            dow_revenue,
            x='Day_of_Week',
            y='Total Revenue',
            title='Revenue by Day of Week',
            labels={'Day_of_Week': 'Day', 'Total Revenue': 'Revenue ($)'},
            template='plotly_white',
            color='Total Revenue',
            color_continuous_scale='Viridis'
        )
        fig_dow.update_layout(height=350)
        st.plotly_chart(fig_dow, use_container_width=True)

    with col_w2:
        weekly_revenue = filtered_df.groupby('Week')['Total Revenue'].sum().reset_index()

        fig_week = px.area(
            weekly_revenue,
            x='Week',
            y='Total Revenue',
            title='Weekly Revenue Trend',
            labels={'Week': 'Week Number', 'Total Revenue': 'Revenue ($)'},
            template='plotly_white'
        )
        fig_week.update_traces(line_color='#2ecc71', fillcolor='rgba(46, 204, 113, 0.3)')
        fig_week.update_layout(height=350)
        st.plotly_chart(fig_week, use_container_width=True)

# Tab 2: Category Analysis
with tab2:
    st.markdown("### Product Category Performance")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        cat_revenue = filtered_df.groupby('Product Category').agg({
            'Total Revenue': 'sum',
            'Units Sold': 'sum'
        }).reset_index().sort_values('Total Revenue', ascending=False)

        fig_cat_bar = px.bar(
            cat_revenue,
            x='Product Category',
            y='Total Revenue',
            title='Revenue by Product Category',
            labels={'Total Revenue': 'Revenue ($)'},
            template='plotly_white',
            color='Product Category'
        )
        fig_cat_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_cat_bar, use_container_width=True)

    with col_c2:
        fig_cat_pie = px.pie(
            cat_revenue,
            values='Total Revenue',
            names='Product Category',
            title='Revenue Distribution by Category',
            hole=0.4,
            template='plotly_white'
        )
        fig_cat_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_cat_pie.update_layout(height=400)
        st.plotly_chart(fig_cat_pie, use_container_width=True)

    # Category vs Region
    st.markdown("#### Category Performance by Region")
    cat_region = filtered_df.groupby(['Product Category', 'Region'])['Total Revenue'].sum().reset_index()
    cat_region_pivot = cat_region.pivot(index='Product Category', columns='Region', values='Total Revenue').fillna(0)

    fig_cat_region = px.bar(
        cat_region,
        x='Product Category',
        y='Total Revenue',
        color='Region',
        title='Revenue by Category and Region',
        labels={'Total Revenue': 'Revenue ($)'},
        template='plotly_white',
        barmode='group'
    )
    fig_cat_region.update_layout(height=400)
    st.plotly_chart(fig_cat_region, use_container_width=True)

    # Top products
    st.markdown("#### Top 10 Products by Revenue")
    top_products = filtered_df.groupby('Product Name')['Total Revenue'].sum().nlargest(10).reset_index()

    fig_top = px.bar(
        top_products,
        x='Total Revenue',
        y='Product Name',
        orientation='h',
        title='Top 10 Products by Revenue',
        labels={'Total Revenue': 'Revenue ($)'},
        template='plotly_white',
        color='Total Revenue',
        color_continuous_scale='RdYlGn'
    )
    fig_top.update_layout(height=450, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)

# Tab 3: Regional Insights
with tab3:
    st.markdown("### Regional Sales Analysis")

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        region_revenue = filtered_df.groupby('Region').agg({
            'Total Revenue': 'sum',
            'Units Sold': 'sum',
            'Transaction ID': 'count'
        }).reset_index()
        region_revenue.columns = ['Region', 'Total Revenue', 'Units Sold', 'Transactions']

        fig_region = px.bar(
            region_revenue,
            x='Region',
            y='Total Revenue',
            title='Total Revenue by Region',
            labels={'Total Revenue': 'Revenue ($)'},
            template='plotly_white',
            color='Region'
        )
        fig_region.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_region, use_container_width=True)

    with col_r2:
        fig_region_pie = px.pie(
            region_revenue,
            values='Total Revenue',
            names='Region',
            title='Revenue Share by Region',
            hole=0.5,
            template='plotly_white'
        )
        fig_region_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_region_pie.update_layout(height=400)
        st.plotly_chart(fig_region_pie, use_container_width=True)

    # Region metrics table
    st.markdown("#### Regional Metrics Comparison")
    region_metrics = filtered_df.groupby('Region').agg({
        'Total Revenue': ['sum', 'mean', 'std'],
        'Units Sold': 'sum',
        'Transaction ID': 'count'
    }).round(2)
    region_metrics.columns = ['Total Revenue', 'Avg Revenue', 'Revenue StdDev', 'Units Sold', 'Transactions']
    region_metrics = region_metrics.reset_index()
    st.dataframe(region_metrics, use_container_width=True, hide_index=True)

    # Regional trend over time
    st.markdown("#### Monthly Revenue Trend by Region")
    region_monthly = filtered_df.groupby(['Month_Name', 'Region'])['Total Revenue'].sum().reset_index()
    region_monthly['Month_Order'] = pd.to_datetime(region_monthly['Month_Name'], format='%B %Y')
    region_monthly = region_monthly.sort_values('Month_Order')

    fig_region_trend = px.line(
        region_monthly,
        x='Month_Name',
        y='Total Revenue',
        color='Region',
        title='Monthly Revenue by Region',
        labels={'Month_Name': 'Month', 'Total Revenue': 'Revenue ($)'},
        template='plotly_white',
        markers=True
    )
    fig_region_trend.update_layout(height=400)
    st.plotly_chart(fig_region_trend, use_container_width=True)

# Tab 4: Payment Methods
with tab4:
    st.markdown("### Payment Method Analysis")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        payment_revenue = filtered_df.groupby('Payment Method').agg({
            'Total Revenue': 'sum',
            'Transaction ID': 'count'
        }).reset_index()
        payment_revenue.columns = ['Payment Method', 'Total Revenue', 'Transaction Count']

        fig_payment = px.bar(
            payment_revenue,
            x='Payment Method',
            y='Total Revenue',
            title='Revenue by Payment Method',
            labels={'Total Revenue': 'Revenue ($)'},
            template='plotly_white',
            color='Payment Method'
        )
        fig_payment.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_payment, use_container_width=True)

    with col_p2:
        fig_payment_pie = px.pie(
            payment_revenue,
            values='Transaction Count',
            names='Payment Method',
            title='Transaction Count by Payment Method',
            hole=0.4,
            template='plotly_white'
        )
        fig_payment_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_payment_pie.update_layout(height=400)
        st.plotly_chart(fig_payment_pie, use_container_width=True)

    # Payment method by category
    st.markdown("#### Payment Method Preference by Category")
    pay_cat = filtered_df.groupby(['Product Category', 'Payment Method']).size().reset_index(name='Count')
    pay_cat_pivot = pay_cat.pivot(index='Product Category', columns='Payment Method', values='Count').fillna(0)

    fig_pay_cat = px.bar(
        pay_cat,
        x='Product Category',
        y='Count',
        color='Payment Method',
        title='Payment Method Usage by Category',
        labels={'Count': 'Number of Transactions'},
        template='plotly_white',
        barmode='stack'
    )
    fig_pay_cat.update_layout(height=400)
    st.plotly_chart(fig_pay_cat, use_container_width=True)

    # Payment method by region
    st.markdown("#### Payment Method by Region")
    pay_region = filtered_df.groupby(['Region', 'Payment Method']).size().reset_index(name='Count')

    fig_pay_region = px.bar(
        pay_region,
        x='Region',
        y='Count',
        color='Payment Method',
        title='Payment Method Usage by Region',
        labels={'Count': 'Number of Transactions'},
        template='plotly_white',
        barmode='group'
    )
    fig_pay_region.update_layout(height=400)
    st.plotly_chart(fig_pay_region, use_container_width=True)

# Tab 5: Data Explorer
with tab5:
    st.markdown("### 📋 Raw Data Explorer")

    # Search and filter within tab
    search_term = st.text_input("🔍 Search by Product Name", "")

    display_df = filtered_df.copy()
    if search_term:
        display_df = display_df[display_df['Product Name'].str.contains(search_term, case=False, na=False)]

    # Show data
    st.dataframe(
        display_df[['Date', 'Product Category', 'Product Name', 'Units Sold', 
                    'Unit Price', 'Total Revenue', 'Region', 'Payment Method']]
        .sort_values('Date', ascending=False)
        .reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

    # Download button
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name=f"filtered_sales_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    # Summary statistics
    st.markdown("#### 📊 Summary Statistics")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("**Revenue Statistics**")
        st.write(filtered_df['Total Revenue'].describe())

    with col_s2:
        st.markdown("**Units Sold Statistics**")
        st.write(filtered_df['Units Sold'].describe())

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #95a5a6;'>📊 Online Sales Dashboard | Built with Streamlit & Plotly</p>", unsafe_allow_html=True)
