#!/usr/bin/env python3

from app import load_data, process_data, filter_data

# Test if our data processing and filtering works
print("Loading and processing data...")
raw_data = load_data()
data = process_data(raw_data)

print(f"Data loaded: {len(data)} rows")
print(f"Apps: {data['app_name'].unique()}")
print(f"Date range: {data['date'].min()} to {data['date'].max()}")

# Test filter function
print("\nTesting filter function...")
app_names = ['BPS', 'Lineup']
device_type = 'all'
date_range = [data['date'].min(), data['date'].max()]

filtered_data = filter_data(app_names, date_range, device_type)
print(f"Filtered data: {len(filtered_data)} rows")

# Test KPI calculations
total_users = filtered_data['distinct_id'].nunique()
valid_sessions = filtered_data[filtered_data['session_id'] != '']['session_id']
total_sessions = valid_sessions.nunique() if len(valid_sessions) > 0 else filtered_data.groupby('distinct_id').size().sum()

print(f"\nKPI Test Results:")
print(f"Total users: {total_users:,}")
print(f"Total sessions: {total_sessions:,}")

# Test widget data
widgets = filtered_data[filtered_data['widget_name'] != '']['widget_name'].value_counts()
print(f"\nTop 5 widgets:")
print(widgets.head())

print("\nTest completed successfully!")