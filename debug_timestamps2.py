from app import load_data, parse_properties
import pandas as pd

# Load raw data
raw_data = load_data()
print('Raw data loaded:', len(raw_data))

# Check what timestamps look like before processing
print('\nRaw timestamp samples:')
for i in range(min(10, len(raw_data))):
    ts = raw_data['timestamp'].iloc[i]
    props = parse_properties(raw_data['properties'].iloc[i])
    widget = props.get('Widget_Name', '')
    print(f'Row {i}: timestamp="{ts}", Widget_Name="{widget}"')

# Parse timestamps and see which rows get filtered
print('\nAfter timestamp parsing:')
parsed_timestamps = pd.to_datetime(raw_data['timestamp'], errors='coerce', format='mixed')

# Check which rows have both valid timestamps AND widget names
print('\nRows with valid timestamps AND widget names:')
count = 0
for i in range(min(1000, len(raw_data))):
    ts = parsed_timestamps.iloc[i]
    props = parse_properties(raw_data['properties'].iloc[i])
    widget = props.get('Widget_Name', '')
    
    if pd.notna(ts) and widget != '':
        count += 1
        if count <= 5:
            print(f'Row {i}: timestamp={ts}, Widget_Name="{widget}"')

print(f'Found {count} rows with both valid timestamps AND widget names in first 1000 rows')