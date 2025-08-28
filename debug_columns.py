from app import load_data

# Test just the data loading
raw_data = load_data()
print('Columns:', raw_data.columns.tolist())
print('Data shape:', raw_data.shape)
print('First few rows:')
print(raw_data.head())