from app import load_data, parse_properties
import pandas as pd

# Load raw data
raw_data = load_data()
print('Raw data loaded:', len(raw_data))

# Step 1: Parse timestamps like process_data does
print('\nStep 1: Parsing timestamps...')
raw_data['timestamp'] = pd.to_datetime(raw_data['timestamp'], errors='coerce', format='mixed')
print('After timestamp parsing:', len(raw_data))
valid_timestamps = raw_data['timestamp'].notna().sum()
print('Valid timestamps:', valid_timestamps)

# Step 2: Remove rows with invalid timestamps
print('\nStep 2: Removing invalid timestamps...')
df = raw_data.dropna(subset=['timestamp'])
print('After removing invalid timestamps:', len(df))

# Step 3: Parse properties
print('\nStep 3: Parsing properties...')
df['props'] = df['properties'].apply(parse_properties)
print('Properties parsed for', len(df), 'rows')

# Check first few props
print('First 3 props:')
for i in range(min(3, len(df))):
    props = df['props'].iloc[i]
    print(f'Row {i}: Widget_Name = "{props.get("Widget_Name", "")}"')

# Step 4: Extract widget names
print('\nStep 4: Extracting widget names...')
df['widget_name'] = df['props'].apply(lambda x: x.get('Widget_Name', '') if isinstance(x, dict) else '')
print('Widget names extracted')

# Check results
non_empty_widgets = len(df[df['widget_name'] != ''])
print(f'Non-empty widget names: {non_empty_widgets}')
print('Top widget names:')
print(df['widget_name'].value_counts().head(10))