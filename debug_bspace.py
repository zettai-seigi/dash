#!/usr/bin/env python3

import pandas as pd

def test_bspace_reading():
    print("Testing different ways to read bspace CSV...")
    
    app = 'bspace'
    
    # Test 1: Standard read
    print("\n1. Standard pandas read:")
    try:
        df1 = pd.read_csv(f'data_app_posthog_{app}.csv', on_bad_lines='skip')
        print(f"   Success: {len(df1)} rows")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 2: Python engine 
    print("\n2. Python engine with skip bad lines:")
    try:
        df2 = pd.read_csv(f'data_app_posthog_{app}.csv', 
                         on_bad_lines='skip', 
                         encoding='utf-8', 
                         engine='python')
        print(f"   Success: {len(df2)} rows")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 3: Python engine with QUOTE_NONE
    print("\n3. Python engine with QUOTE_NONE:")
    try:
        df3 = pd.read_csv(f'data_app_posthog_{app}.csv', 
                         on_bad_lines='skip',
                         encoding='utf-8',
                         quoting=3,  # QUOTE_NONE
                         engine='python')
        print(f"   Success: {len(df3)} rows")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 4: Check the actual line count
    print("\n4. Checking actual file line count:")
    try:
        with open(f'data_app_posthog_{app}.csv', 'r', encoding='utf-8', errors='ignore') as f:
            lines = sum(1 for line in f)
            print(f"   Total lines in file: {lines}")
    except Exception as e:
        print(f"   Failed to count lines: {e}")

if __name__ == "__main__":
    test_bspace_reading()