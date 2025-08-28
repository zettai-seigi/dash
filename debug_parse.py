from app import load_data, parse_properties
import pandas as pd

# Load raw data
raw_data = load_data()
print('Raw data rows:', len(raw_data))

# Test the parsing function on first row
props_str = raw_data['properties'].iloc[0]
print(f'Properties string type: {type(props_str)}')
print(f'Properties string length: {len(props_str)}')
print(f'First 200 chars: {props_str[:200]}')

# Test parsing step by step
print('\n=== Testing parsing steps ===')
parsed = parse_properties(props_str)
print(f'Parsed result type: {type(parsed)}')
print(f'Parsed result: {parsed}')

# Check if Widget_Name is in the string
if 'Widget_Name' in props_str:
    print('\nWidget_Name found in string!')
    idx = props_str.find('Widget_Name')
    snippet = props_str[idx-50:idx+150]
    print(f'Context around Widget_Name: {snippet}')
else:
    print('\nWidget_Name NOT found in string')
    # Check what keys ARE available
    if 'Page_Name' in props_str:
        print('Page_Name found')
    if 'Duration' in props_str:
        print('Duration found')
    if '"$' in props_str:
        print('System properties with $ found')