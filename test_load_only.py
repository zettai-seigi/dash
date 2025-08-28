import pandas as pd
import csv

# Test the CSV loading directly
app = 'BPS'
try:
    with open(f'data_app_posthog_{app}.csv', 'r', encoding='utf-8', errors='ignore') as file:
        lines = []
        csv_reader = csv.reader(file, quotechar='"', delimiter=',')
        header = next(csv_reader)  # Skip header
        print('CSV Header:', header[:10], '...', header[-5:])
        
        for i, row in enumerate(csv_reader):
            if i >= 5:  # Just test first 5 rows
                break
            print(f'Row {i} length: {len(row)}')
            if len(row) >= 157:
                uuid = row[0]
                event = row[1]
                distinct_id = row[152]
                timestamp = row[156]
                
                # Properties reconstruction
                props_parts = row[2:152]
                props_parts = [part for part in props_parts if part.strip()]
                properties = ','.join(props_parts)
                
                print(f'  uuid: {uuid}')
                print(f'  event: {event}')
                print(f'  distinct_id: {distinct_id}')
                print(f'  timestamp: {timestamp}')
                print(f'  properties length: {len(properties)}')
                
                lines.append({
                    'uuid': uuid,
                    'event': event,
                    'properties': properties,
                    'distinct_id': distinct_id,
                    'timestamp': timestamp
                })
            else:
                print(f'  Row too short: {len(row)} columns')
        
        df = pd.DataFrame(lines)
        print(f'Created DataFrame with {len(df)} rows')
        print('Columns:', df.columns.tolist())
        print('Sample data:')
        print(df.head(2))
        
except Exception as e:
    print(f'Error: {e}')