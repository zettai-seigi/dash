#!/usr/bin/env python3

import pandas as pd
import json

def investigate_missing_widget_data():
    """Investigate why bspace, btech, etam might be missing widget data"""
    
    print("🔍 INVESTIGATING MISSING WIDGET DATA")
    print("=" * 50)
    
    apps = ['BPS', 'Lineup', 'bspace', 'btech', 'etam']
    
    for app in apps:
        print(f"\n📊 Analyzing {app}:")
        print("-" * 30)
        
        try:
            # Load sample data
            df = pd.read_csv(f'data_app_posthog_{app}.csv', nrows=1000, on_bad_lines='skip')
            print(f"✅ Loaded {len(df)} sample rows")
            
            # Check for widget_name data
            widget_count = 0
            tab_count = 0
            route_count = 0
            
            for i, prop_str in enumerate(df['properties'].head(500)):
                if pd.notna(prop_str) and prop_str != '':
                    try:
                        props = json.loads(prop_str)
                        if 'Widget_Name' in props and props['Widget_Name'] != '':
                            widget_count += 1
                        if 'Tab_Name' in props and props['Tab_Name'] != '':
                            tab_count += 1
                        if 'Route' in props and props['Route'] != '':
                            route_count += 1
                    except:
                        # Try basic string search for malformed JSON
                        if 'Widget_Name' in prop_str:
                            widget_count += 1
                        if 'Tab_Name' in prop_str:
                            tab_count += 1
                        if 'Route' in prop_str:
                            route_count += 1
            
            print(f"  🎯 Widget_Name entries: {widget_count}/500 ({widget_count/5:.1f}%)")
            print(f"  📂 Tab_Name entries: {tab_count}/500 ({tab_count/5:.1f}%)")
            print(f"  🗺️ Route entries: {route_count}/500 ({route_count/5:.1f}%)")
            
            # Check what widgets are actually found
            if widget_count > 0:
                widget_names = []
                for i, prop_str in enumerate(df['properties'].head(500)):
                    if pd.notna(prop_str) and prop_str != '':
                        try:
                            props = json.loads(prop_str)
                            if 'Widget_Name' in props and props['Widget_Name'] != '':
                                widget_names.append(props['Widget_Name'])
                        except:
                            import re
                            match = re.search(r'"Widget_Name":\s*"([^"]*)"', prop_str)
                            if match and match.group(1):
                                widget_names.append(match.group(1))
                
                unique_widgets = list(set(widget_names))[:10]  # Show first 10
                print(f"  📝 Sample widgets found: {unique_widgets}")
            else:
                print(f"  ❌ No Widget_Name data found in {app}")
                
        except Exception as e:
            print(f"❌ Error loading {app}: {e}")

if __name__ == "__main__":
    investigate_missing_widget_data()