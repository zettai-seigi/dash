#!/usr/bin/env python3

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Create sample data that mimics the real structure
print("Creating sample data...")

sample_data = []
apps = ['BPS', 'Lineup', 'bspace', 'btech', 'etam']

for app in apps:
    for i in range(1000):  # 1000 rows per app
        sample_data.append({
            'uuid': f'sample-{app}-{i}',
            'event': 'Capture',
            'properties': f'{{"Widget_Name": "Button_{i%20}", "Page_Name": "Page_{i%10}", "Duration": {np.random.randint(10, 300)}, "$device_type": "{"Mobile" if i%2 else "Desktop"}", "$session_id": "session_{i//10}"}}',
            'distinct_id': f'user{i%100}@{app.lower()}.com',
            'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 30)),
            'app_name': app
        })

df = pd.DataFrame(sample_data)
print(f"Created {len(df)} sample rows")

# Test the KPI calculation functions directly
total_users = df['distinct_id'].nunique()
valid_sessions = df[df['properties'].str.contains('session_')]['properties'].str.extract(r'session_(\d+)')[0].nunique()

print(f"Total users: {total_users}")
print(f"Total sessions: {valid_sessions}")
print("Sample data creation successful!")