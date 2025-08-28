from app import load_data, parse_properties
import pandas as pd

raw_data = load_data()
print('Raw data loaded:', len(raw_data))

# Check timestamps
print('\nTimestamp analysis:')
print('Raw timestamps sample:')
print(raw_data['timestamp'].head())

# Parse timestamps
print('\nParsing timestamps...')
timestamps = pd.to_datetime(raw_data['timestamp'], errors='coerce', format='mixed')
print('Valid timestamps:', timestamps.notna().sum())
print('Invalid timestamps:', timestamps.isna().sum())

# Filter out invalid timestamps like the app does
valid_data = raw_data.dropna(subset=['timestamp'])
print('After dropping NaN timestamps:', len(valid_data))

# Now check widget names in valid data
print('\nWidget names in valid data:')
widget_count = 0
for i in range(min(100, len(valid_data))):
    props_str = valid_data['properties'].iloc[i]
    parsed = parse_properties(props_str)
    if parsed.get('Widget_Name', '') != '':
        widget_count += 1
        if widget_count <= 5:
            print(f'Row {i}: Widget_Name = "{parsed.get("Widget_Name")}"')

print(f'Found {widget_count} rows with Widget_Name in first 100 valid rows')