from app import load_data, parse_properties
import pandas as pd

# Load raw data
raw_data = load_data()
print('Raw data rows:', len(raw_data))

# Test the parsing function on first few rows
print('\nTesting parse_properties on first 5 rows:')
for i in range(min(5, len(raw_data))):
    props_str = raw_data['properties'].iloc[i]
    parsed = parse_properties(props_str)
    print(f'Row {i}:')
    print(f'  Widget_Name: {parsed.get("Widget_Name", "NOT_FOUND")}')
    print(f'  Page_Name: {parsed.get("Page_Name", "NOT_FOUND")}')
    print(f'  Props keys: {list(parsed.keys())[:10]}')
    print('---')

# Check if Widget_Name exists in any raw properties at all
print('\nChecking if Widget_Name exists in raw properties...')
found_widget = False
for i in range(min(100, len(raw_data))):
    props_str = raw_data['properties'].iloc[i]
    if 'Widget_Name' in props_str:
        found_widget = True
        print(f'Found Widget_Name in row {i}')
        # Show a snippet around Widget_Name
        idx = props_str.find('Widget_Name')
        snippet = props_str[max(0, idx-50):idx+100]
        print(f'Snippet: {snippet}')
        break

if not found_widget:
    print('Widget_Name not found in first 100 properties strings')
    # Show what IS in the properties
    sample_prop = raw_data['properties'].iloc[0]
    print(f'Sample properties (first 500 chars): {sample_prop[:500]}')