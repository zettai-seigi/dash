#!/usr/bin/env python3

import pandas as pd
import json
import re

def deep_widget_analysis():
    """Deep analysis of widget data across all apps"""
    
    print("🔍 DEEP WIDGET DATA ANALYSIS")
    print("=" * 60)
    
    apps = ['BPS', 'Lineup', 'bspace', 'btech', 'etam']
    
    for app in apps:
        print(f"\n📊 DEEP ANALYSIS FOR {app.upper()}:")
        print("-" * 40)
        
        try:
            # Load more data for thorough analysis
            df = pd.read_csv(f'data_app_posthog_{app}.csv', nrows=5000, on_bad_lines='skip')
            print(f"✅ Loaded {len(df)} rows for analysis")
            
            widget_found = 0
            tab_found = 0
            page_found = 0
            sample_widgets = []
            sample_tabs = []
            sample_pages = []
            
            for i, prop_str in enumerate(df['properties']):
                if pd.notna(prop_str) and prop_str != '':
                    try:
                        # Try JSON parsing first
                        props = json.loads(prop_str)
                        
                        if 'Widget_Name' in props and props['Widget_Name'] != '':
                            widget_found += 1
                            if len(sample_widgets) < 5:
                                sample_widgets.append(props['Widget_Name'])
                        
                        if 'Tab_Name' in props and props['Tab_Name'] != '':
                            tab_found += 1
                            if len(sample_tabs) < 5:
                                sample_tabs.append(props['Tab_Name'])
                        
                        if 'Page_Name' in props and props['Page_Name'] != '':
                            page_found += 1
                            if len(sample_pages) < 5:
                                sample_pages.append(props['Page_Name'])
                                
                    except json.JSONDecodeError:
                        # Try regex for malformed JSON
                        widget_match = re.search(r'"Widget_Name":\s*"([^"]*)"', prop_str)
                        if widget_match and widget_match.group(1).strip():
                            widget_found += 1
                            if len(sample_widgets) < 5:
                                sample_widgets.append(widget_match.group(1))
                        
                        tab_match = re.search(r'"Tab_Name":\s*"([^"]*)"', prop_str)
                        if tab_match and tab_match.group(1).strip():
                            tab_found += 1
                            if len(sample_tabs) < 5:
                                sample_tabs.append(tab_match.group(1))
                        
                        page_match = re.search(r'"Page_Name":\s*"([^"]*)"', prop_str)
                        if page_match and page_match.group(1).strip():
                            page_found += 1
                            if len(sample_pages) < 5:
                                sample_pages.append(page_match.group(1))
            
            total_rows = len(df)
            print(f"  🎯 Widget_Name: {widget_found}/{total_rows} ({widget_found/total_rows*100:.1f}%)")
            print(f"  📂 Tab_Name: {tab_found}/{total_rows} ({tab_found/total_rows*100:.1f}%)")
            print(f"  📄 Page_Name: {page_found}/{total_rows} ({page_found/total_rows*100:.1f}%)")
            
            if sample_widgets:
                print(f"  📝 Sample Widgets: {sample_widgets}")
            else:
                print(f"  ❌ No Widget_Name data found")
            
            if sample_tabs:
                print(f"  📁 Sample Tabs: {sample_tabs}")
            
            if sample_pages:
                print(f"  📃 Sample Pages: {sample_pages}")
            
            # Check for alternative interaction data
            print(f"\n  🔍 Alternative interaction indicators:")
            
            # Check for screen_name, element interactions, etc.
            screen_found = 0
            event_types = {}
            
            for i, row in df.iterrows():
                if i >= 1000:  # Limit to first 1000 for performance
                    break
                    
                # Check event types
                event = row.get('event', '')
                if event:
                    event_types[event] = event_types.get(event, 0) + 1
                
                # Check for screen_name in properties
                prop_str = row.get('properties', '')
                if pd.notna(prop_str) and prop_str != '':
                    if '$screen_name' in prop_str:
                        screen_found += 1
            
            print(f"    📱 $screen_name entries: {screen_found}/1000")
            print(f"    📊 Event types: {dict(list(event_types.items())[:5])}")
            
        except Exception as e:
            print(f"❌ Error analyzing {app}: {e}")

if __name__ == "__main__":
    deep_widget_analysis()