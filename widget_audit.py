#!/usr/bin/env python3

import re

def audit_dashboard_widgets():
    """Audit all widgets in the Streamlit dashboard for per-app utilization"""
    
    print("🔍 DASHBOARD WIDGET AUDIT - Per-App Utilization Check")
    print("=" * 60)
    
    with open('streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Find all tabs
    tab_pattern = r'with tab(\d+):\s*\n\s*st\.header\("([^"]+)"\)'
    tabs = re.findall(tab_pattern, content)
    
    print(f"📊 Found {len(tabs)} main tabs:")
    for tab_num, tab_name in tabs:
        print(f"  Tab {tab_num}: {tab_name}")
    
    print("\n" + "=" * 60)
    
    # Check each tab for widgets
    tab_sections = content.split('with tab')
    
    for i, section in enumerate(tab_sections[1:], 1):  # Skip first section before tabs
        # Extract tab name
        header_match = re.search(r'st\.header\("([^"]+)"\)', section)
        tab_name = header_match.group(1) if header_match else f"Tab {i}"
        
        print(f"\n📊 {tab_name.upper()}")
        print("-" * 50)
        
        # Find all charts/widgets in this tab
        chart_patterns = [
            (r'st\.plotly_chart\(([^,]+),', "Plotly Chart"),
            (r'px\.([a-z_]+)\(', "Plotly Express"),
            (r'go\.([A-Z][a-z]+)\(', "Plotly Graph Objects"),
            (r'st\.dataframe\(', "Data Table"),
            (r'st\.metric\(', "Metric Widget"),
            (r'fig = ([^=]+)', "Figure Creation")
        ]
        
        widgets_found = []
        
        for pattern, widget_type in chart_patterns:
            matches = re.findall(pattern, section)
            if matches:
                widgets_found.extend([(widget_type, match) for match in matches])
        
        # Look for app differentiation indicators
        app_indicators = [
            'color=.*app_name',
            'groupby.*app_name',
            'app_name.*unique',
            'filtered_data.*app_name',
            'by.*app',
            'color_discrete_map',
            'facet_col.*app'
        ]
        
        app_aware_count = 0
        for indicator in app_indicators:
            if re.search(indicator, section, re.IGNORECASE):
                app_aware_count += 1
        
        # Extract titles for better identification
        title_matches = re.findall(r'title[=\s]*[\'"]([^\'"]+)[\'"]', section)
        
        print(f"  📈 Total widgets found: {len(set([w[0] for w in widgets_found]))}")
        print(f"  🎯 App-aware indicators: {app_aware_count}")
        
        if title_matches:
            print(f"  📊 Chart titles found:")
            for title in set(title_matches[:5]):  # Show first 5 unique titles
                app_aware = any(keyword in title.lower() for keyword in ['app', 'application', 'by app'])
                status = "✅ App-aware" if app_aware else "❓ Check needed"
                print(f"    • {title} - {status}")
        
        # Check for missing app differentiation
        single_aggregations = re.findall(r'\.groupby\([\'"]([^\'"]+)[\'"]\)', section)
        non_app_groupbys = [g for g in single_aggregations if 'app' not in g.lower()]
        
        if non_app_groupbys:
            print(f"  ⚠️  Potential missing app breakdown:")
            for groupby in set(non_app_groupbys[:3]):
                print(f"    • groupby('{groupby}') - consider adding app_name")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    print("  1. Ensure all charts use 'color=app_name' or equivalent")
    print("  2. Add app differentiation to widgets without it")
    print("  3. Use consistent color schemes across apps")
    print("  4. Consider facet_col='app_name' for complex comparisons")

if __name__ == "__main__":
    audit_dashboard_widgets()