#!/usr/bin/env python3

import pandas as pd
import json
from collections import Counter

def analyze_available_parameters():
    print("🔍 Analyzing available parameters in our data...")
    
    # Load a sample of data to see what parameters we have
    try:
        df = pd.read_csv('data_app_posthog_BPS.csv', nrows=1000, on_bad_lines='skip')
        print(f"✅ Loaded sample data: {len(df)} rows")
        print(f"📊 Columns: {df.columns.tolist()}")
        
        # Analyze the properties column to see what parameters are available
        print("\n🔍 Analyzing properties JSON to find available parameters...")
        
        all_params = Counter()
        sample_props = []
        
        for i, prop_str in enumerate(df['properties'].head(100)):
            if pd.notna(prop_str) and prop_str != '':
                try:
                    props = json.loads(prop_str)
                    all_params.update(props.keys())
                    if i < 5:  # Show first 5 examples
                        sample_props.append(props)
                except:
                    # Try basic parsing
                    import re
                    matches = re.findall(r'"([^"]+)":', prop_str)
                    all_params.update(matches)
        
        print(f"\n📈 Found {len(all_params)} unique parameters:")
        for param, count in all_params.most_common(30):
            print(f"  • {param}: {count} occurrences")
        
        print(f"\n📝 Sample properties structures:")
        for i, props in enumerate(sample_props):
            print(f"\nExample {i+1}:")
            for key, value in list(props.items())[:10]:  # Show first 10 keys
                print(f"  {key}: {value}")
        
        return all_params
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        return None

if __name__ == "__main__":
    analyze_available_parameters()