from app import load_data, process_data

# Load and process data like the app does
raw_data = load_data()
data = process_data(raw_data)

print('Total rows:', len(data))
print('Widget_name column exists:', 'widget_name' in data.columns)
print('Sample widget_name values:')
print(data['widget_name'].value_counts().head(10))
print()
non_empty = data[data['widget_name'] != '']
print('Non-empty widget names:', len(non_empty))
print('Empty widget names:', len(data) - len(non_empty))
print()
print('First few widget names:', list(data['widget_name'].head(10)))

# Test the actual filtering used in the callback
print('\nActual callback filtering test:')
filtered_for_widgets = data[data['widget_name'] != '']
print('After filtering for non-empty widget names:', len(filtered_for_widgets))

if len(filtered_for_widgets) > 0:
    widget_counts = filtered_for_widgets.groupby('widget_name').size().reset_index(name='count')
    widget_counts = widget_counts.sort_values('count', ascending=False).head(15)
    print('Top widget counts:')
    print(widget_counts)
else:
    print('No widget data after filtering!')