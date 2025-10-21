"""
data_processing.py

Fetches SaaS funnel data from MySQL and computes:
- Funnel stages & conversion
- Revenue metrics (MRR, ARPU, churn)
- Cohort retention
- Weekly growth metrics
- Plan-wise metrics
- Traffic source metrics

Uses raw SQL + pandas + python-dateutil parser
"""

import logging
from typing import Dict, Optional
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser

from db_connection import create_connection, close_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Fetch raw data
# -----------------------------
def fetch_raw_data(conn) -> Dict[str, pd.DataFrame]:
    """Fetch core tables from MySQL"""
    logger.info("Fetching raw data from DB...")
    users = pd.read_sql("SELECT * FROM Users;", conn)
    events = pd.read_sql("SELECT * FROM Events;", conn)
    plans = pd.read_sql("SELECT * FROM Plans;", conn)
    sources = pd.read_sql("SELECT * FROM Sources;", conn)

    # Convert dates
    if 'signup_date' in users.columns:
        users['signup_date'] = pd.to_datetime(users['signup_date'])
    if 'event_date' in events.columns:
        events['event_date'] = pd.to_datetime(events['event_date'])

    logger.info("Fetched: %d users, %d events", len(users), len(events))
    return {'users': users, 'events': events, 'plans': plans, 'sources': sources}

# -----------------------------
# Funnel metrics
# -----------------------------
def compute_funnel(events_df: pd.DataFrame, stages: Optional[list] = None) -> pd.DataFrame:
    if stages is None:
        stages = ['visit', 'signup', 'trial', 'paid']

    counts = events_df.groupby('event_type')['user_id'].nunique().reindex(stages).fillna(0).astype(int)
    df = pd.DataFrame({'users': counts})
    start = df['users'].iloc[0] if len(df) > 0 else 0
    df['conversion_from_start_pct'] = (df['users'] / (start if start > 0 else 1) * 100).round(2)
    df['conversion_from_prev_pct'] = df['users'].pct_change().fillna(1).apply(lambda x: round(x * 100 if x != 1 else 100, 2))
    df['drop_off_pct_from_prev'] = (100 - df['conversion_from_prev_pct']).round(2)
    df.index.name = 'stage'
    return df

# -----------------------------
# Revenue metrics
# -----------------------------
def compute_revenue_metrics(users_df: pd.DataFrame,
                            events_df: pd.DataFrame,
                            plans_df: pd.DataFrame,
                            as_of_date: Optional[datetime] = None) -> Dict[str, float]:
    if as_of_date is None:
        as_of_date = datetime.utcnow()

    paid_events = events_df[events_df['event_type'] == 'paid'].copy()
    paid_users = paid_events['user_id'].unique()
    paid_count = len(paid_users)

    merged = users_df[users_df['user_id'].isin(paid_users)].merge(plans_df, on='plan_id', how='left')
    mrr = merged['price'].sum() if 'price' in merged.columns else 0.0
    arpu = (mrr / len(users_df)) if len(users_df) > 0 else 0.0
    avg_rev_per_paid = merged['price'].mean() if len(merged) > 0 else 0.0

    last_30 = as_of_date - timedelta(days=30)
    recent_paid = paid_events[paid_events['event_date'] >= last_30]['user_id'].nunique()
    churn_rate = 100 * (1 - (recent_paid / paid_count)) if paid_count > 0 else 0.0

    return {
        'paid_count': int(paid_count),
        'mrr': round(mrr, 2),
        'arpu': round(arpu, 2),
        'avg_rev_per_paid_user': round(avg_rev_per_paid, 2),
        'churn_rate_pct_30d': round(churn_rate, 2)
    }

# -----------------------------
# Cohort retention
# -----------------------------
def compute_cohort_retention(users_df: pd.DataFrame, events_df: pd.DataFrame, cohort_by: str = 'week') -> pd.DataFrame:
    df_users = users_df[['user_id', 'signup_date']].copy()
    if cohort_by == 'week':
        df_users['cohort'] = df_users['signup_date'].dt.to_period('W').apply(lambda r: r.start_time)
    elif cohort_by == 'month':
        df_users['cohort'] = df_users['signup_date'].dt.to_period('M').apply(lambda r: r.start_time)
    else:
        raise ValueError("cohort_by must be 'week' or 'month'")

    df_events = events_df[['user_id', 'event_date']].copy()
    merged = df_events.merge(df_users, on='user_id', how='inner')
    merged['period_number'] = ((merged['event_date'] - merged['signup_date']).dt.days // 7).astype(int)

    if merged.empty:
        logger.warning("No data available for cohort calculation.")
        return pd.DataFrame()

    cohort_pivot = (
        merged.groupby(['cohort', 'period_number'])['user_id']
        .nunique()
        .reset_index()
        .pivot(index='cohort', columns='period_number', values='user_id')
    ).fillna(0)

    cohort_sizes = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_sizes, axis=0).multiply(100).round(2)
    return retention

# -----------------------------
# Weekly growth
# -----------------------------
def compute_weekly_growth(users_df: pd.DataFrame, events_df: pd.DataFrame, metric: str = 'signups', weeks: int = 12) -> pd.DataFrame:
    now = datetime.utcnow()
    start = now - timedelta(weeks=weeks)
    metric_map = {'signups': 'signup', 'visits': 'visit', 'trials': 'trial', 'paid': 'paid'}

    if metric == 'active_users':
        events = events_df[events_df['event_date'] >= start].copy()
        events['week'] = events['event_date'].dt.to_period('W').apply(lambda r: r.start_time)
        series = events.groupby('week')['user_id'].nunique().rename('value')
    else:
        evt = metric_map.get(metric)
        if evt is None:
            raise ValueError("Unsupported metric")
        events = events_df[(events_df['event_type'] == evt) & (events_df['event_date'] >= start)].copy()
        events['week'] = events['event_date'].dt.to_period('W').apply(lambda r: r.start_time)
        series = events.groupby('week')['user_id'].nunique().rename('value')

    ts = series.reset_index().sort_values('week')
    ts['pct_change'] = ts['value'].pct_change().fillna(0).apply(lambda x: round(x * 100, 2))
    ts = ts.rename(columns={'week': 'week_start'})

    if ts.empty:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['week_start', 'value', 'pct_change'])
    
    idx = pd.date_range(start=ts['week_start'].min(), end=ts['week_start'].max(), freq='7D')
    ts = ts.set_index('week_start').reindex(idx, fill_value=0).rename_axis('week_start').reset_index()
    return ts

# -----------------------------
# Plan-wise metrics
# -----------------------------
def compute_plan_metrics(users_df: pd.DataFrame, events_df: pd.DataFrame, plans_df: pd.DataFrame) -> pd.DataFrame:
    paid_events = events_df[events_df['event_type'] == 'paid'].copy()
    merged = users_df.merge(paid_events[['user_id']], on='user_id', how='inner')
    merged = merged.merge(plans_df, on='plan_id', how='left')

    plan_metrics = merged.groupby('plan_name').agg(
        paid_users=('user_id', 'nunique'),
        mrr=('price', 'sum'),
        avg_revenue_per_user=('price', 'mean')
    ).reset_index()
    return plan_metrics

# -----------------------------
# Traffic source metrics
# -----------------------------
def compute_source_metrics(users_df: pd.DataFrame, events_df: pd.DataFrame, sources_df: pd.DataFrame) -> pd.DataFrame:
    paid_events = events_df[events_df['event_type'] == 'paid'].copy()
    merged = users_df.merge(paid_events[['user_id']], on='user_id', how='inner')
    merged = merged.merge(sources_df, on='source_id', how='left')

    source_metrics = merged.groupby('source_name').agg(
        paid_users=('user_id', 'nunique')
    ).reset_index()
    return source_metrics

# -----------------------------
# Runner
# -----------------------------
def run_all_metrics() -> Dict[str, pd.DataFrame]:
    conn = create_connection()
    if not conn:
        raise RuntimeError("DB connection failed")
    try:
        raw = fetch_raw_data(conn)
        users, events, plans, sources = raw['users'], raw['events'], raw['plans'], raw['sources']

        funnel_df = compute_funnel(events)
        revenue_dict = compute_revenue_metrics(users, events, plans)
        cohort_df = compute_cohort_retention(users, events)
        weekly_growth_df = compute_weekly_growth(users, events, metric='signups')
        plan_metrics_df = compute_plan_metrics(users, events, plans)
        source_metrics_df = compute_source_metrics(users, events, sources)

        return {
            'funnel': funnel_df,
            'revenue': revenue_dict,
            'cohort': cohort_df,
            'weekly_growth': weekly_growth_df,
            'plan_metrics': plan_metrics_df,
            'source_metrics': source_metrics_df
        }
    finally:
        close_connection(conn)

# -----------------------------
# Runner: CSV Uploads
# -----------------------------
def run_all_metrics_from_csv(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Compute all metrics from uploaded CSV files.
    data_dict keys: 'users', 'events', 'plans', 'sources' -> pd.DataFrame
    """
    users, events, plans, sources = data_dict['users'], data_dict['events'], data_dict['plans'], data_dict['sources']

    # After reading the CSVs into DataFrames
    users['signup_date'] = pd.to_datetime(users['signup_date'], errors='coerce')
    events['event_date'] = pd.to_datetime(events['event_date'], errors='coerce')

    # Core metrics
    funnel_df = compute_funnel(events)
    revenue_dict = compute_revenue_metrics(users, events, plans)
    cohort_df = compute_cohort_retention(users, events)
    weekly_growth_df = compute_weekly_growth(users, events, metric='signups')

    # New metrics
    plan_metrics_df = compute_plan_metrics(users, events, plans)
    source_metrics_df = compute_source_metrics(users, events, sources)

    


    return {
        'funnel': funnel_df,
        'revenue': revenue_dict,
        'cohort': cohort_df,
        'weekly_growth': weekly_growth_df,
        'plan_metrics': plan_metrics_df,
        'source_metrics': source_metrics_df
    }        

# -----------------------------
# Test runner
# -----------------------------
if __name__ == "__main__":
    results = run_all_metrics()
    print("=== Funnel ===")
    print(results['funnel'])
    print("\n=== Revenue ===")
    print(results['revenue'])
    print("\n=== Cohort Sample ===")
    print(results['cohort'].head())
    print("\n=== Weekly Growth ===")
    print(results['weekly_growth'].head())
    print("\n=== Plan Metrics ===")
    print(results['plan_metrics'])
    print("\n=== Source Metrics ===")
    print(results['source_metrics'])
