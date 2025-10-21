import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from data_processing import run_all_metrics, run_all_metrics_from_csv

# -------------------------------
# Page config & theme
# -------------------------------
st.set_page_config(page_title="SaaS Funnel Dashboard", layout="wide")
st.markdown(
    """
    <style>
    body { background-color: #1e1e1e; color: #ffffff; }
    .stButton>button { background-color: #ff6600; color: white; }
    </style>
    """, unsafe_allow_html=True
)
st.title("🚀 SaaS Funnel & Conversion Dashboard")

# -------------------------------
# Sidebar: Choose data source
# -------------------------------
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Select data source:", ["MySQL", "Upload CSV"])

# -------------------------------
# CSV upload option
# -------------------------------
uploaded_data = {}
if data_source == "Upload CSV":
    st.sidebar.info("Upload the required CSV files (Users, Events, Plans, Sources)")
    uploaded_data['users'] = st.sidebar.file_uploader("Users CSV", type="csv")
    uploaded_data['events'] = st.sidebar.file_uploader("Events CSV", type="csv")
    uploaded_data['plans'] = st.sidebar.file_uploader("Plans CSV", type="csv")
    uploaded_data['sources'] = st.sidebar.file_uploader("Sources CSV", type="csv")

# -------------------------------
# Sidebar filters
# -------------------------------
lookback_days = st.sidebar.selectbox(
    "Lookback Period (Days)",
    options=[7, 14, 30, 60, 90, 180, 365],
    index=2
)
event_options = st.sidebar.multiselect(
    "Event Types",
    options=['visit', 'signup', 'trial', 'paid'],
    default=['visit', 'signup', 'trial', 'paid']
)

# -------------------------------
# Fetch metrics
# -------------------------------
with st.spinner("Fetching metrics..."):
    if data_source == "MySQL":
        results = run_all_metrics()
    else:
        # Check if all files uploaded
        if all(uploaded_data.values()):
            # Read CSVs into DataFrames
            df_dict = {k: pd.read_csv(v) for k, v in uploaded_data.items()}
            results = run_all_metrics_from_csv(df_dict)
        else:
            st.warning("Please upload all required CSV files.")
            st.stop()

# -------------------------------
# Apply lookback filter
# -------------------------------
cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

funnel_df = results['funnel'].loc[results['funnel'].index.isin(event_options)]
weekly_growth_df = results['weekly_growth'][results['weekly_growth']['week_start'] >= cutoff_date].copy()
cohort_df = results['cohort'].copy()
revenue = results['revenue']
plan_metrics_df = results['plan_metrics']
source_metrics_df = results['source_metrics']

# -------------------------------
# Tabs for metrics
# -------------------------------
tabs = st.tabs(["Funnel", "Revenue", "Cohort Retention", "Weekly Growth", "Plan Metrics", "Source Metrics"])

# -------------------------------
# Funnel Tab
# -------------------------------
with tabs[0]:
    st.subheader("📊 Funnel Conversion")
    funnel_fig = px.bar(
        funnel_df.reset_index(),
        x='stage',
        y='users',
        text='users',
        title="Funnel Stages",
        labels={'users': 'Number of Users', 'stage': 'Stage'},
        height=400,
        color_discrete_sequence=['#ff6600']
    )
    funnel_fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white')
    funnel_fig.update_traces(textposition='outside')
    st.plotly_chart(funnel_fig, use_container_width=True)
    st.download_button("Download Funnel Data", funnel_df.reset_index().to_csv(), "funnel.csv")

# -------------------------------
# Revenue Tab
# -------------------------------
with tabs[1]:
    st.subheader("💰 Revenue Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Paid Users", revenue['paid_count'])
    col2.metric("MRR ($)", revenue['mrr'])
    col3.metric("ARPU ($)", revenue['arpu'])
    col4.metric("Avg Revenue / Paid User", revenue['avg_rev_per_paid_user'])
    col5.metric("Churn Rate (%)", revenue['churn_rate_pct_30d'])

# -------------------------------
# Cohort Retention Tab
# -------------------------------
with tabs[2]:
    st.subheader("🧩 Cohort Retention (%)")
    if not cohort_df.empty:
        cohort_fig = px.imshow(
            cohort_df.values,
            labels=dict(x="Week Since Signup", y="Cohort Start Week", color="Retention %"),
            x=[str(c) for c in cohort_df.columns],
            y=[str(c.date()) for c in cohort_df.index],
            color_continuous_scale=px.colors.sequential.Oranges,
        )
        cohort_fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white')
        st.plotly_chart(cohort_fig, use_container_width=True)
        st.download_button("Download Cohort Data", cohort_df.to_csv(), "cohort.csv")
    else:
        st.info("Cohort data not available.")

# -------------------------------
# Weekly Growth Tab
# -------------------------------
with tabs[3]:
    st.subheader("📈 Weekly Growth")
    weekly_fig = px.line(
        weekly_growth_df,
        x='week_start',
        y='value',
        text='pct_change',
        title=f"Weekly Signups Growth - Last {lookback_days} Days",
        labels={'week_start': 'Week Start', 'value': 'Signups'},
        height=400
    )
    weekly_fig.update_traces(mode='lines+markers+text', textposition='top center', line_color='#ff6600')
    weekly_fig.update_layout(plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white')
    st.plotly_chart(weekly_fig, use_container_width=True)
    st.download_button("Download Weekly Growth Data", weekly_growth_df.to_csv(), "weekly_growth.csv")

# -------------------------------
# Plan Metrics Tab
# -------------------------------
with tabs[4]:
    st.subheader("📊 Plan Metrics")
    st.dataframe(plan_metrics_df.style.format({"mrr": "{:.2f}", "avg_revenue_per_user": "{:.2f}"}))
    st.download_button("Download Plan Metrics", plan_metrics_df.to_csv(), "plan_metrics.csv")

# -------------------------------
# Source Metrics Tab
# -------------------------------
with tabs[5]:
    st.subheader("🌐 Traffic Source Metrics")
    st.dataframe(source_metrics_df)
    st.download_button("Download Source Metrics", source_metrics_df.to_csv(), "source_metrics.csv")
