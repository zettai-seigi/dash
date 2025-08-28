from app import load_data, process_data, parse_properties

# Test the full pipeline
raw_data = load_data()
print('Raw data loaded:', len(raw_data))

# Test parsing a few rows manually
print('\nManual parsing test:')
for i in range(min(5, len(raw_data))):
    props_str = raw_data['properties'].iloc[i]
    parsed = parse_properties(props_str)
    print(f'Row {i}: Widget_Name = "{parsed.get("Widget_Name", "")}"')

# Process the data
processed_data = process_data(raw_data)
print(f'\nProcessed data: {len(processed_data)} rows')

# Check widget_name extraction
print('\nWidget name extraction:')
print('Total widget_name values:', len(processed_data['widget_name']))
print('Non-empty widget_name:', len(processed_data[processed_data['widget_name'] != '']))
print('Sample widget_name values:')
print(processed_data['widget_name'].value_counts().head())

# Debug the props column
print('\nChecking props column:')
first_props = processed_data['props'].iloc[0]
print('First props type:', type(first_props))
print('First props content:', first_props)

# Check if the apply function is working
print('\nTesting apply function manually:')
test_row = processed_data['props'].iloc[0]
if isinstance(test_row, dict):
    print('First row Widget_Name from dict:', test_row.get('Widget_Name', 'NOT_FOUND'))
else:
    print('First row props is not a dict:', type(test_row))