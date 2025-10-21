import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -----------------------------
# Paths
# -----------------------------
data_dir = "/Users/ayyanchoudhary/da_projects/SaaS-Funnel-Dashboard/data"  # relative to your project root
os.makedirs(data_dir, exist_ok=True)

# -----------------------------
# Generate dummy Users.csv
# -----------------------------
n_users = 100
users = pd.DataFrame({
    "user_id": range(1, n_users+1),
    "signup_date": [datetime(2025,1,1) + timedelta(days=np.random.randint(0, 100)) for _ in range(n_users)],
    "plan_id": np.random.randint(1, 4, size=n_users),
    "source_id": np.random.randint(1, 5, size=n_users)
})
users.to_csv(os.path.join(data_dir, "Users.csv"), index=False)

# -----------------------------
# Generate dummy Plans.csv
# -----------------------------
plans = pd.DataFrame({
    "plan_id": [1,2,3],
    "plan_name": ["Basic", "Standard", "Pro"],
    "price": [10.0, 20.0, 50.0]
})
plans.to_csv(os.path.join(data_dir, "Plans.csv"), index=False)

# -----------------------------
# Generate dummy Sources.csv
# -----------------------------
sources = pd.DataFrame({
    "source_id": [1,2,3,4],
    "source_name": ["Google Ads", "Organic", "Referral", "Social Media"]
})
sources.to_csv(os.path.join(data_dir, "Sources.csv"), index=False)

# -----------------------------
# Generate dummy Events.csv
# -----------------------------
event_types = ['visit','signup','trial','paid']
events = pd.DataFrame({
    "user_id": np.random.choice(users['user_id'], 300),
    "event_type": np.random.choice(event_types, 300),
    "event_date": [datetime(2025,1,1) + timedelta(days=np.random.randint(0, 100)) for _ in range(300)]
})
events.to_csv(os.path.join(data_dir, "Events.csv"), index=False)

print(f"Dummy CSV files generated in folder: {data_dir}")
