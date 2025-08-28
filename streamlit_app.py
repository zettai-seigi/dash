#!/usr/bin/env python3

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="📊 Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stTab {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load all CSV files and combine them"""
    apps = ['BPS', 'Lineup', 'bspace', 'btech', 'etam']
    all_data = []
    
    for app in apps:
        try:
            # Read the CSV with multiple fallback strategies for malformed files
            df = None
            
            # Strategy 1: Standard pandas read
            try:
                df = pd.read_csv(f'data_app_posthog_{app}.csv', on_bad_lines='skip')
                st.write(f"✅ Standard read successful for {app}: {len(df)} rows")
            except Exception as e1:
                st.write(f"⚠️ Standard read failed for {app}: {e1}")
                
                # Strategy 2: Read with Python engine and skip bad lines
                try:
                    df = pd.read_csv(f'data_app_posthog_{app}.csv', 
                                   on_bad_lines='skip', 
                                   encoding='utf-8', 
                                   engine='python')
                    st.write(f"✅ Python engine read successful for {app}: {len(df)} rows")
                except Exception as e2:
                    st.write(f"⚠️ Python engine read failed for {app}: {e2}")
                    
                    # Strategy 3: Read with different quoting strategy
                    try:
                        df = pd.read_csv(f'data_app_posthog_{app}.csv', 
                                       on_bad_lines='skip',
                                       encoding='utf-8',
                                       quoting=3,  # QUOTE_NONE
                                       engine='python')
                        st.write(f"✅ Quote-none read successful for {app}: {len(df)} rows")
                    except Exception as e3:
                        st.write(f"❌ All read strategies failed for {app}: {e3}")
            
            if df is not None:
                # Select only the columns we need
                required_cols = ['uuid', 'event', 'properties', 'distinct_id', 'timestamp']
                available_cols = [col for col in required_cols if col in df.columns]
                df = df[available_cols].copy()
                
                df['app_name'] = app
                all_data.append(df)
                st.write(f"📊 Successfully processed {app}: {len(df)} rows")
            else:
                st.error(f"❌ Failed to load {app} - creating sample data")
                # Create sample data if file doesn't exist
                sample_data = {
                    'uuid': [f'sample-{app}-{i}' for i in range(100)],
                    'event': ['Capture'] * 100,
                    'properties': ['{}'] * 100,
                    'distinct_id': [f'user{i}@example.com' for i in range(100)],
                    'timestamp': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(100)],
                    'app_name': [app] * 100
                }
                df = pd.DataFrame(sample_data)
                all_data.append(df)
        except Exception as e:
            st.error(f"❌ Error loading {app}: {e}")
            # Create sample data if file doesn't exist
            sample_data = {
                'uuid': [f'sample-{app}-{i}' for i in range(100)],
                'event': ['Capture'] * 100,
                'properties': ['{}'] * 100,
                'distinct_id': [f'user{i}@example.com' for i in range(100)],
                'timestamp': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(100)],
                'app_name': [app] * 100
            }
            df = pd.DataFrame(sample_data)
            all_data.append(df)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    st.write(f"🎯 **Total combined data: {len(combined_df)} rows across {len(all_data)} applications**")
    return combined_df

def parse_properties(properties_str):
    """Parse JSON properties string safely"""
    try:
        if pd.isna(properties_str) or properties_str == '':
            return {}
        
        # Try standard JSON parsing first
        try:
            return json.loads(properties_str)
        except:
            # Try with quote replacements
            try:
                fixed = properties_str.replace('\\"', '"').replace('""', '"')
                return json.loads(fixed)
            except:
                # For malformed JSON, try to extract key fields directly with regex
                result = {}
                
                # Extract common fields using regex patterns
                patterns = {
                    'Widget_Name': r'"Widget_Name":\s*"([^"]*)"',
                    'Page_Name': r'"Page_Name":\s*"([^"]*)"', 
                    'Duration': r'"Duration":\s*(\d+)',
                    '$device_type': r'"\$device_type":\s*"([^"]*)"',
                    '$os': r'"\$os":\s*"([^"]*)"',
                    '$geoip_country_name': r'"\$geoip_country_name":\s*"([^"]*)"',
                    '$session_id': r'"\$session_id":\s*"([^"]*)"',
                    '$screen_name': r'"\$screen_name":\s*"([^"]*)"',
                    'Connection': r'"Connection":\s*(true|false)',
                    '$network_wifi': r'"\$network_wifi":\s*(true|false)'
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, properties_str)
                    if match:
                        value = match.group(1)
                        if key in ['Duration']:
                            result[key] = int(value)
                        elif key in ['Connection', '$network_wifi']:
                            result[key] = value.lower() == 'true'
                        else:
                            result[key] = value
                
                return result
    except:
        return {}

@st.cache_data
def process_data(df):
    """Process and clean the data"""
    # Parse timestamps with error handling
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
    
    # Remove rows with invalid timestamps
    df = df.dropna(subset=['timestamp'])
    
    # Parse properties JSON
    df['props'] = df['properties'].apply(parse_properties)
    
    # Extract key metrics from properties
    df['duration'] = df['props'].apply(lambda x: x.get('Duration', 0) if isinstance(x, dict) else 0)
    df['page_name'] = df['props'].apply(lambda x: x.get('Page_Name', '') if isinstance(x, dict) else '')
    df['device_type'] = df['props'].apply(lambda x: x.get('$device_type', 'Unknown') if isinstance(x, dict) else 'Unknown')
    df['os'] = df['props'].apply(lambda x: x.get('$os', 'Unknown') if isinstance(x, dict) else 'Unknown')
    df['country'] = df['props'].apply(lambda x: x.get('$geoip_country_name', 'Unknown') if isinstance(x, dict) else 'Unknown')
    df['session_id'] = df['props'].apply(lambda x: x.get('$session_id', '') if isinstance(x, dict) else '')
    df['connection'] = df['props'].apply(lambda x: x.get('Connection', None) if isinstance(x, dict) else None)
    df['network_wifi'] = df['props'].apply(lambda x: x.get('$network_wifi', None) if isinstance(x, dict) else None)
    df['widget_name'] = df['props'].apply(lambda x: x.get('Widget_Name', '') if isinstance(x, dict) else '')
    df['screen_name'] = df['props'].apply(lambda x: x.get('$screen_name', '') if isinstance(x, dict) else '')
    
    # Extract additional parameters from the article for advanced analytics
    df['tab_name'] = df['props'].apply(lambda x: x.get('Tab_Name', '') if isinstance(x, dict) else '')
    df['route'] = df['props'].apply(lambda x: x.get('Route', '') if isinstance(x, dict) else '')
    df['prev_route'] = df['props'].apply(lambda x: x.get('Prev_Route', '') if isinstance(x, dict) else '')
    df['checkin'] = df['props'].apply(lambda x: x.get('CheckIn', '') if isinstance(x, dict) else '')
    df['checkout'] = df['props'].apply(lambda x: x.get('CheckOut', '') if isinstance(x, dict) else '')
    df['connection'] = df['props'].apply(lambda x: x.get('Connection', None) if isinstance(x, dict) else None)
    df['app_version'] = df['props'].apply(lambda x: x.get('$app_version', '') if isinstance(x, dict) else '')
    df['app_build'] = df['props'].apply(lambda x: x.get('$app_build', '') if isinstance(x, dict) else '')
    
    # Parse GPS coordinates - check both direct and $set nested locations
    def extract_gps(props):
        if not isinstance(props, dict):
            return None, None, None
        
        # Check $set nested object first
        gps_data = props.get('$set', props) if '$set' in props else props
        
        lat = gps_data.get('$geoip_latitude')
        lon = gps_data.get('$geoip_longitude')
        city = gps_data.get('$geoip_city_name')
        
        return lat, lon, city
    
    df[['latitude', 'longitude', 'city']] = df['props'].apply(
        lambda x: pd.Series(extract_gps(x))
    )
    
    # Create location string for filtering
    df['location'] = df.apply(
        lambda row: f"{row['city']}, {row['country']}" if row['city'] and row['city'] != 'Unknown' else row['country'],
        axis=1
    )
    
    # Flag Indonesia locations (rough coordinate bounds)
    try:
        df['is_indonesia'] = df.apply(
            lambda row: (
                row['country'] == 'Indonesia' or 
                (pd.notna(row['latitude']) and pd.notna(row['longitude']) and
                 -11 <= row['latitude'] <= 6 and 95 <= row['longitude'] <= 141)
            ), axis=1
        )
    except Exception as e:
        # Fallback: just use country name
        df['is_indonesia'] = df['country'] == 'Indonesia'
    
    # Create date column
    df['date'] = df['timestamp'].dt.date
    
    # Parse checkin/checkout timestamps for session analysis
    df['checkin_time'] = pd.to_datetime(df['checkin'], errors='coerce')
    df['checkout_time'] = pd.to_datetime(df['checkout'], errors='coerce')
    
    return df

def filter_data(data, app_names, date_range, device_type, selected_country='All Countries'):
    """Filter data based on user selections"""
    filtered_data = data[data['app_name'].isin(app_names)]
    
    if date_range:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data['date'] >= start_date) &
            (filtered_data['date'] <= end_date)
        ]
    
    if device_type != 'All':
        filtered_data = filtered_data[filtered_data['device_type'] == device_type]
    
    if selected_country != 'All Countries':
        filtered_data = filtered_data[filtered_data['country'] == selected_country]
    
    return filtered_data

# Load and process data
@st.cache_data
def get_processed_data():
    raw_data = load_data()
    return process_data(raw_data)

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Usage & Usability Insights for 5 Applications</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data with status display
    with st.expander("📁 Data Loading Status", expanded=False):
        st.write("Loading CSV files...")
        data = get_processed_data()
        st.success("Data loading completed!")
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filter Controls")
    
    # App filter
    app_names = st.sidebar.multiselect(
        "🏢 Applications",
        options=data['app_name'].unique(),
        default=data['app_name'].unique()
    )
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "📅 Date Range",
        value=(data['date'].min(), data['date'].max()),
        min_value=data['date'].min(),
        max_value=data['date'].max()
    )
    
    # Device filter
    device_types = ['All'] + list(data['device_type'].unique())
    device_type = st.sidebar.selectbox(
        "📱 Device Type",
        options=device_types,
        index=0
    )
    
    # Location filter  
    available_countries = ['All Countries'] + sorted(list(data['country'].unique()))
    selected_country = st.sidebar.selectbox(
        "🌍 Country Filter",
        options=available_countries,
        index=0,
        help="Filter data by country/location"
    )
    
    # Filter data
    if app_names:
        filtered_data = filter_data(data, app_names, date_range, device_type, selected_country)
    else:
        st.warning("Please select at least one application")
        return
    
    # KPI Metrics
    st.header("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = filtered_data['distinct_id'].nunique()
        st.metric("👥 Total Users", f"{total_users:,}")
    
    with col2:
        valid_sessions = filtered_data[filtered_data['session_id'] != '']['session_id']
        total_sessions = valid_sessions.nunique() if len(valid_sessions) > 0 else filtered_data.groupby('distinct_id').size().sum()
        st.metric("🔄 Total Sessions", f"{total_sessions:,}")
    
    with col3:
        valid_durations = filtered_data[filtered_data['duration'] > 0]['duration']
        avg_duration = valid_durations.mean() if len(valid_durations) > 0 else 0
        st.metric("⏱️ Avg Duration", f"{avg_duration:.1f}s")
    
    with col4:
        if len(valid_sessions) > 0:
            session_durations = filtered_data.groupby('session_id')['duration'].max()
            short_sessions = len(session_durations[session_durations < 30])
            bounce_rate = (short_sessions / len(session_durations) * 100)
        else:
            short_sessions = len(filtered_data[filtered_data['duration'] < 30])
            bounce_rate = (short_sessions / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
        st.metric("📉 Bounce Rate", f"{bounce_rate:.1f}%")
    
    # Tabs for different dashboard views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Executive Overview", "📱 Usage Analytics", "🎯 Usability Insights", "⚡ Technical Performance", "🚀 Advanced Usage Analytics"])
    
    with tab1:
        st.header("📊 Executive Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily Active Users
            daily_users = filtered_data.groupby(['date', 'app_name'])['distinct_id'].nunique().reset_index()
            fig = px.line(daily_users, x='date', y='distinct_id', color='app_name',
                         title='Daily Active Users by App',
                         labels={'distinct_id': 'Daily Active Users', 'date': 'Date'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # App Comparison
            app_metrics = filtered_data.groupby('app_name').agg({
                'distinct_id': 'nunique',
                'duration': 'mean',
                'event': 'count'
            }).reset_index()
            app_metrics.columns = ['App', 'Users', 'Avg Duration', 'Events']
            
            # Create a simpler chart to avoid Plotly dual-axis issues
            fig = go.Figure()
            
            # Add bar chart for users (left axis)
            fig.add_trace(go.Bar(
                x=app_metrics['App'], 
                y=app_metrics['Users'], 
                name='Users',
                yaxis='y',
                offsetgroup=1
            ))
            
            # Add line chart for duration (right axis) 
            fig.add_trace(go.Scatter(
                x=app_metrics['App'], 
                y=app_metrics['Avg Duration'], 
                mode='lines+markers', 
                name='Avg Duration (s)',
                yaxis='y2',
                line=dict(color='orange', width=3),
                marker=dict(size=8, color='orange')
            ))
            
            # Update layout with dual y-axes
            fig.update_layout(
                title_text="App Comparison: Users vs Average Duration",
                xaxis=dict(title="Application"),
                yaxis=dict(
                    title="Number of Users",
                    side="left"
                ),
                yaxis2=dict(
                    title="Average Duration (seconds)",
                    side="right",
                    overlaying="y"
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Geographic Distribution by App
        geo_data = filtered_data.groupby(['country', 'app_name'])['distinct_id'].nunique().reset_index()
        # Get top 10 countries by total users
        top_countries = filtered_data.groupby('country')['distinct_id'].nunique().sort_values(ascending=False).head(10).index
        geo_data_filtered = geo_data[geo_data['country'].isin(top_countries)]
        
        fig = px.bar(geo_data_filtered, x='distinct_id', y='country', color='app_name', orientation='h',
                     title='Top 10 Countries by User Count & App',
                     labels={'distinct_id': 'Number of Users', 'country': 'Country'})
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("📱 Usage Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Session Duration Distribution by App
            valid_durations = filtered_data[filtered_data['duration'] > 0]
            fig = px.histogram(valid_durations, x='duration', color='app_name', nbins=30, 
                             title='Session Duration Distribution by App',
                             labels={'duration': 'Duration (seconds)', 'count': 'Frequency'},
                             marginal="box")  # Add box plot on side
            fig.update_layout(barmode='overlay')
            fig.update_traces(opacity=0.7)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top Widgets by App (Stacked)
            widget_data = filtered_data[filtered_data['widget_name'] != '']
            widget_by_app = widget_data.groupby(['widget_name', 'app_name']).size().reset_index(name='usage_count')
            
            # Get top 15 widgets overall
            top_widgets = widget_data['widget_name'].value_counts().head(15).index
            widget_by_app_filtered = widget_by_app[widget_by_app['widget_name'].isin(top_widgets)]
            
            fig = px.bar(widget_by_app_filtered, y='widget_name', x='usage_count', color='app_name',
                        title='Top 15 Widgets Usage by App',
                        labels={'usage_count': 'Usage Count', 'widget_name': 'Widget Name'},
                        orientation='h')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Full width widget analysis
        st.subheader("🎯 Detailed Widget Analysis by Application")
        
        # Overall heatmap first
        widget_matrix = filtered_data[filtered_data['widget_name'] != ''].groupby(['app_name', 'widget_name']).size().reset_index(name='usage_count')
        
        # Create pivot for heatmap
        if len(widget_matrix) > 0:
            # Get top widgets for readability
            top_widgets_detailed = filtered_data[filtered_data['widget_name'] != '']['widget_name'].value_counts().head(20).index
            widget_matrix_filtered = widget_matrix[widget_matrix['widget_name'].isin(top_widgets_detailed)]
            
            pivot_matrix = widget_matrix_filtered.pivot(index='widget_name', columns='app_name', values='usage_count').fillna(0)
            
            fig = px.imshow(pivot_matrix, 
                           title='Widget Usage Heatmap: Apps vs Widgets (Top 20 Widgets Overall)',
                           labels=dict(x="Application", y="Widget Name", color="Usage Count"),
                           aspect="auto")
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Individual app widget analysis
            st.subheader("📱 Individual App Widget Analysis")
            
            # Create tabs for each app
            app_list = sorted(filtered_data['app_name'].unique())
            if len(app_list) > 1:
                app_tabs = st.tabs([f"📊 {app}" for app in app_list])
                
                for i, app in enumerate(app_list):
                    with app_tabs[i]:
                        app_data = filtered_data[filtered_data['app_name'] == app]
                        app_widgets = app_data[app_data['widget_name'] != '']
                        
                        # Determine what interaction data is available for this app
                        has_widgets = len(app_widgets) > 0
                        has_tabs = len(app_data[app_data['tab_name'] != '']) > 0
                        has_pages = len(app_data[app_data['page_name'] != '']) > 0
                        has_events = len(app_data) > 0
                        
                        if has_widgets:
                            # Full widget analysis for BPS and Lineup
                            col_app1, col_app2 = st.columns(2)
                            
                            with col_app1:
                                # Top widgets for this app
                                app_widget_counts = app_widgets['widget_name'].value_counts().head(15)
                                
                                fig = px.bar(
                                    x=app_widget_counts.values,
                                    y=app_widget_counts.index,
                                    orientation='h',
                                    title=f'Top 15 Widgets in {app}',
                                    labels={'x': 'Usage Count', 'y': 'Widget Name'},
                                    color=app_widget_counts.values,
                                    color_continuous_scale='Blues'
                                )
                                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with col_app2:
                                # Widget usage over time for this app
                                app_widgets['date'] = pd.to_datetime(app_widgets['timestamp']).dt.date
                                widget_time_data = app_widgets.groupby(['date', 'widget_name']).size().reset_index(name='usage_count')
                                
                                # Get top 5 widgets for time series
                                top_5_widgets = app_widget_counts.head(5).index
                                widget_time_filtered = widget_time_data[widget_time_data['widget_name'].isin(top_5_widgets)]
                                
                                if len(widget_time_filtered) > 0:
                                    fig = px.line(widget_time_filtered, x='date', y='usage_count', 
                                                color='widget_name',
                                                title=f'Top 5 Widget Usage Over Time - {app}',
                                                labels={'usage_count': 'Daily Usage Count', 'date': 'Date'})
                                    fig.update_layout(height=500)
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info(f"Not enough time series data for {app}")
                            
                            # Widget performance metrics table
                            st.subheader(f"📊 Widget Performance Metrics - {app}")
                            
                            widget_metrics = app_widgets.groupby('widget_name').agg({
                                'distinct_id': 'nunique',
                                'duration': 'mean',
                                'session_id': 'nunique',
                                'uuid': 'count'
                            }).reset_index()
                            widget_metrics.columns = ['Widget', 'Unique Users', 'Avg Duration', 'Sessions', 'Total Uses']
                            widget_metrics['Avg Uses per User'] = (widget_metrics['Total Uses'] / widget_metrics['Unique Users']).round(2)
                            widget_metrics = widget_metrics.sort_values('Total Uses', ascending=False).head(20)
                            
                            st.dataframe(widget_metrics, use_container_width=True)
                            
                        elif has_tabs or has_pages:
                            # Tab/Page analysis for ETAM (and others with limited widget data)
                            st.info(f"📝 {app} uses Tab/Page tracking instead of individual widget tracking")
                            
                            col_app1, col_app2 = st.columns(2)
                            
                            if has_tabs:
                                with col_app1:
                                    # Tab analysis
                                    app_tab_data = app_data[app_data['tab_name'] != '']
                                    tab_counts = app_tab_data['tab_name'].value_counts().head(15)
                                    
                                    fig = px.bar(
                                        x=tab_counts.values,
                                        y=tab_counts.index,
                                        orientation='h',
                                        title=f'Top 15 Tab Usage in {app}',
                                        labels={'x': 'Usage Count', 'y': 'Tab Name'},
                                        color=tab_counts.values,
                                        color_continuous_scale='Greens'
                                    )
                                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            if has_pages:
                                with col_app2:
                                    # Page analysis
                                    app_page_data = app_data[app_data['page_name'] != '']
                                    page_counts = app_page_data['page_name'].value_counts().head(15)
                                    
                                    fig = px.bar(
                                        x=page_counts.values,
                                        y=page_counts.index,
                                        orientation='h',
                                        title=f'Top 15 Page Usage in {app}',
                                        labels={'x': 'Usage Count', 'y': 'Page Name'},
                                        color=page_counts.values,
                                        color_continuous_scale='Oranges'
                                    )
                                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            # User engagement analysis
                            st.subheader(f"👥 User Engagement Analysis - {app}")
                            
                            # Create user segments based on session count
                            user_sessions = app_data.groupby('distinct_id')['session_id'].nunique().reset_index()
                            user_sessions['user_segment'] = user_sessions['session_id'].apply(
                                lambda x: 'New User (1 session)' if x == 1 
                                else 'Regular (2-5 sessions)' if x <= 5 
                                else 'Power User (6+ sessions)'
                            )
                            
                            # Engagement metrics by segment
                            app_data_with_segments = app_data.merge(
                                user_sessions[['distinct_id', 'user_segment']], 
                                on='distinct_id', 
                                how='left'
                            )
                            
                            segment_metrics = app_data_with_segments.groupby('user_segment').agg({
                                'duration': 'mean',
                                'distinct_id': 'nunique',
                                'tab_name': lambda x: len([t for t in x if t != '']),
                                'page_name': lambda x: len([p for p in x if p != ''])
                            }).round(2)
                            segment_metrics.columns = ['Avg Duration', 'Users', 'Tab Interactions', 'Page Interactions']
                            segment_metrics = segment_metrics.reset_index()
                            
                            st.dataframe(segment_metrics, use_container_width=True)
                            
                        elif app in ['bspace', 'btech']:
                            # Event-based analysis for bspace and btech
                            st.info(f"📱 {app} uses web-based event tracking ($autocapture, $pageview, $pageleave)")
                            
                            col_app1, col_app2 = st.columns(2)
                            
                            with col_app1:
                                # Event type distribution
                                event_counts = app_data['event'].value_counts().head(10)
                                
                                fig = px.pie(values=event_counts.values, names=event_counts.index,
                                           title=f'Event Type Distribution - {app}')
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with col_app2:
                                # Daily activity
                                app_data['date'] = pd.to_datetime(app_data['timestamp']).dt.date
                                daily_activity = app_data.groupby('date').agg({
                                    'distinct_id': 'nunique',
                                    'event': 'count'
                                }).reset_index()
                                
                                fig = px.line(daily_activity, x='date', y='distinct_id',
                                            title=f'Daily Active Users - {app}',
                                            labels={'distinct_id': 'Active Users', 'date': 'Date'})
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # User behavior summary
                            st.subheader(f"👥 User Behavior Summary - {app}")
                            
                            behavior_summary = app_data.groupby('distinct_id').agg({
                                'event': 'count',
                                'duration': 'mean',
                                'session_id': 'nunique'
                            }).round(2)
                            behavior_summary.columns = ['Total Events', 'Avg Duration', 'Sessions']
                            
                            # Show summary statistics
                            summary_stats = behavior_summary.describe().round(2)
                            st.dataframe(summary_stats, use_container_width=True)
                            
                        else:
                            st.warning(f"No interaction data available for {app}")
            else:
                st.info("Select multiple apps to see individual analysis")
        
        # Platform and Usage Patterns
        col3, col4 = st.columns(2)
        
        with col3:
            # Platform Breakdown by App (Enhanced)
            platform_data = filtered_data.groupby(['device_type', 'app_name'])['distinct_id'].nunique().reset_index()
            fig = px.bar(platform_data, x='app_name', y='distinct_id', color='device_type',
                        title='Platform Breakdown by App',
                        labels={'distinct_id': 'Number of Users', 'app_name': 'Application'})
            
            # Add percentage annotations
            app_totals = platform_data.groupby('app_name')['distinct_id'].sum()
            for trace in fig.data:
                app = trace.x[0] if len(trace.x) > 0 else None
                if app and app in app_totals:
                    trace.text = [f"{val}<br>({val/app_totals[app]*100:.1f}%)" for val in trace.y]
                    trace.textposition = "inside"
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # Hourly Usage Pattern by App
            filtered_data['hour'] = filtered_data['timestamp'].dt.hour
            hourly_usage = filtered_data.groupby(['hour', 'app_name'])['distinct_id'].nunique().reset_index()
            fig = px.line(hourly_usage, x='hour', y='distinct_id', color='app_name',
                         title='Hourly Usage Pattern by App',
                         labels={'distinct_id': 'Active Users', 'hour': 'Hour of Day'})
            fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
            st.plotly_chart(fig, use_container_width=True)
        
        # Additional analytics
        col5, col6 = st.columns(2)
        
        with col5:
            # Page/Screen Usage by App
            page_data = filtered_data[filtered_data['page_name'] != '']
            page_by_app = page_data.groupby(['page_name', 'app_name']).size().reset_index(name='visits')
            top_pages = page_data['page_name'].value_counts().head(10).index
            page_by_app_filtered = page_by_app[page_by_app['page_name'].isin(top_pages)]
            
            fig = px.bar(page_by_app_filtered, y='page_name', x='visits', color='app_name',
                        title='Top 10 Pages/Screens by App',
                        labels={'visits': 'Visit Count', 'page_name': 'Page/Screen Name'},
                        orientation='h')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col6:
            # Session Count Distribution by App
            session_counts = filtered_data[filtered_data['session_id'] != ''].groupby(['app_name', 'distinct_id'])['session_id'].nunique().reset_index()
            session_counts.columns = ['app_name', 'user', 'session_count']
            
            fig = px.box(session_counts, x='app_name', y='session_count', color='app_name',
                        title='Session Count Distribution by App',
                        labels={'session_count': 'Sessions per User', 'app_name': 'Application'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("🎯 Usability Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Engagement Analysis (Duration vs Sessions) by App
            user_engagement = filtered_data.groupby(['distinct_id', 'app_name']).agg({
                'duration': 'mean',
                'session_id': 'nunique'
            }).reset_index()
            user_engagement = user_engagement[user_engagement['session_id'] > 0]
            
            fig = px.scatter(user_engagement, x='session_id', y='duration', color='app_name',
                           title='User Engagement: Sessions vs Average Duration by App',
                           labels={'session_id': 'Number of Sessions', 'duration': 'Average Duration (s)'},
                           hover_data=['distinct_id'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Screen/Page Popularity by App
            page_data = filtered_data[filtered_data['page_name'] != ''].groupby(['page_name', 'app_name']).size().reset_index(name='visits')
            top_pages = page_data.groupby('page_name')['visits'].sum().sort_values(ascending=False).head(10).index
            page_data_filtered = page_data[page_data['page_name'].isin(top_pages)]
            
            fig = px.sunburst(page_data_filtered, 
                            path=['page_name', 'app_name'], 
                            values='visits',
                            title='Top 10 Page Popularity by App')
            st.plotly_chart(fig, use_container_width=True)
        
        # User Journey Analysis - Enhanced with Bar Chart
        if len(filtered_data[filtered_data['page_name'] != '']) > 0:
            journey_data = filtered_data[filtered_data['page_name'] != ''].groupby(['page_name', 'app_name']).size().reset_index(name='visits')
            journey_data = journey_data.sort_values('visits', ascending=False).head(20)
            
            # Create treemap
            fig = px.treemap(journey_data, path=['app_name', 'page_name'], values='visits',
                           title='User Journey: Page Visits by Application (Treemap)')
            st.plotly_chart(fig, use_container_width=True)
            
            # Create comprehensive bar chart for user journey
            st.subheader("📊 Complete User Journey Bar Chart - All Apps")
            
            # Get all page visits with app breakdown
            all_journey_data = filtered_data[filtered_data['page_name'] != ''].groupby(['page_name', 'app_name']).agg({
                'distinct_id': 'nunique',
                'duration': 'mean',
                'widget_name': lambda x: len([w for w in x if w != ''])
            }).reset_index()
            all_journey_data.columns = ['page_name', 'app_name', 'unique_users', 'avg_duration', 'widget_interactions']
            
            # Sort by total visits to show most popular pages
            page_totals = all_journey_data.groupby('page_name')['unique_users'].sum().sort_values(ascending=False)
            top_pages = page_totals.head(15).index
            filtered_journey = all_journey_data[all_journey_data['page_name'].isin(top_pages)]
            
            # Create comprehensive bar chart
            fig = px.bar(filtered_journey, 
                        x='unique_users', 
                        y='page_name', 
                        color='app_name',
                        orientation='h',
                        title='User Journey: Top 15 Pages Across All Apps',
                        labels={'unique_users': 'Unique Users', 'page_name': 'Page/Screen Name'},
                        hover_data=['avg_duration', 'widget_interactions'])
            
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=600,
                showlegend=True,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Add journey flow analysis
            st.subheader("🔄 Page-to-Page Journey Flow Analysis")
            
            # Check available navigation data
            has_route_data = len(filtered_data[(filtered_data['route'] != '') & (filtered_data['prev_route'] != '')]) > 0
            has_page_data = len(filtered_data[filtered_data['page_name'] != '']) > 0
            
            if has_route_data or has_page_data:
                # Journey analysis options and filters
                st.subheader("🎛️ Journey Analysis Controls")
                
                # Main controls row - now 3 columns for per-app filter
                journey_col1, journey_col2, journey_col3 = st.columns(3)
                
                with journey_col1:
                    analysis_type = st.selectbox(
                        "Journey Analysis Type",
                        ["Navigation Flow Chart", "Sankey Flow Diagram", "User Path Analysis", "Drop-off Analysis"],
                        help="Choose different ways to analyze user journey patterns"
                    )
                
                with journey_col2:
                    # Select data source for journey analysis
                    if has_route_data and has_page_data:
                        data_source = st.selectbox("Data Source", ["Routes", "Page Names"], help="Choose between route data or page name data")
                    elif has_route_data:
                        data_source = "Routes"
                        st.info("Using route navigation data")
                    else:
                        data_source = "Page Names"
                        st.info("Using page name data")
                
                with journey_col3:
                    # Per-app filter directly in main controls
                    journey_apps_main = ['All Apps'] + sorted(list(filtered_data['app_name'].unique()))
                    selected_app_main = st.selectbox(
                        "🏢 Focus App",
                        options=journey_apps_main,
                        help="Focus journey analysis on specific app",
                        key="journey_app_main"
                    )
                
                # Advanced filters in expandable section
                with st.expander("🔍 Journey Analysis Filters", expanded=False):
                    filter_col1, filter_col2, filter_col3 = st.columns(3)
                    
                    with filter_col1:
                        # User type filter (moved from having the app filter here)
                        min_journey_length = st.number_input(
                            "Min Journey Steps",
                            min_value=1,
                            max_value=20,
                            value=1,
                            help="Filter to users with at least N navigation steps"
                        )
                        
                        # User activity filter
                        active_users_only = st.checkbox(
                            "Active Users Only",
                            help="Show only users with multiple navigation actions",
                            value=False
                        )
                    
                    with filter_col2:
                        # Time-based filters
                        journey_time_filter = st.selectbox(
                            "Journey Time Period",
                            ["All Time", "Last 7 Days", "Last 30 Days", "Custom Range"],
                            help="Filter journeys by time period"
                        )
                        
                        if journey_time_filter == "Custom Range":
                            custom_start = st.date_input("Journey Start Date", value=filtered_data['date'].min())
                            custom_end = st.date_input("Journey End Date", value=filtered_data['date'].max())
                        
                        # Session duration filter with debug info
                        if filtered_data['duration'].notna().any():
                            # Duration analysis
                            duration_stats = filtered_data['duration'].describe()
                            non_zero_durations = filtered_data[filtered_data['duration'] > 0]['duration']
                            
                            # Show debug information
                            # Page analysis for current selection
                            with st.expander("📄 Page Analysis Debug", expanded=False):
                                current_pages = filtered_data['page_name'].value_counts().head(20)
                                st.write("**Top 20 Pages in Current Selection:**")
                                for page, count in current_pages.items():
                                    if page and page.strip():  # Only show non-empty pages
                                        st.write(f"• **{page}**: {count} visits")
                                
                                # Search for login-related pages
                                login_keywords = ['login', 'signin', 'auth', 'sign', 'entrance', 'portal']
                                login_pages = []
                                for page in filtered_data['page_name'].unique():
                                    if page and any(keyword.lower() in str(page).lower() for keyword in login_keywords):
                                        count = filtered_data[filtered_data['page_name'] == page].shape[0]
                                        login_pages.append((page, count))
                                
                                if login_pages:
                                    st.write("**🔑 Login-related Pages Found:**")
                                    for page, count in login_pages:
                                        st.write(f"• **{page}**: {count} visits")
                                else:
                                    st.write("**🔍 No login-related pages found with keywords:** login, signin, auth, sign, entrance, portal")
                            
                            with st.expander("📊 Duration Data Debug", expanded=False):
                                col_debug1, col_debug2 = st.columns(2)
                                with col_debug1:
                                    st.write("**Duration Statistics:**")
                                    st.write(f"• Total records: {len(filtered_data):,}")
                                    st.write(f"• Records with duration > 0: {len(non_zero_durations):,}")
                                    st.write(f"• % with valid duration: {len(non_zero_durations)/len(filtered_data)*100:.1f}%")
                                    st.write(f"• Min duration: {duration_stats['min']:.1f}s")
                                    st.write(f"• Max duration: {duration_stats['max']:.1f}s")
                                with col_debug2:
                                    st.write("**Duration Percentiles:**")
                                    st.write(f"• 50th (median): {duration_stats['50%']:.1f}s")
                                    st.write(f"• 75th: {duration_stats['75%']:.1f}s")
                                    st.write(f"• 90th: {filtered_data['duration'].quantile(0.90):.1f}s")
                                    st.write(f"• 95th: {filtered_data['duration'].quantile(0.95):.1f}s")
                                    st.write(f"• 99th: {filtered_data['duration'].quantile(0.99):.1f}s")
                            
                            # Use better max value logic
                            duration_max = max(
                                int(filtered_data['duration'].max()),
                                int(filtered_data['duration'].quantile(0.99)),
                                300  # Minimum fallback
                            )
                            
                            session_duration_filter = st.slider(
                                "Session Duration (seconds)",
                                min_value=0,
                                max_value=duration_max,
                                value=(0, min(duration_max, int(filtered_data['duration'].quantile(0.95)) if filtered_data['duration'].quantile(0.95) > 0 else 300)),
                                help=f"Filter by session duration range. Max available: {duration_max}s"
                            )
                        else:
                            session_duration_filter = None
                    
                    with filter_col3:
                        # Page/Route specific filters
                        if data_source == "Routes" and has_route_data:
                            available_routes = sorted(list(set(
                                filtered_data['route'].dropna().tolist() + 
                                filtered_data['prev_route'].dropna().tolist()
                            )))
                            if available_routes:
                                selected_routes = st.multiselect(
                                    "Include Routes",
                                    options=available_routes,
                                    default=available_routes[:10],  # Show top 10 by default
                                    help="Select specific routes to include in analysis"
                                )
                            else:
                                selected_routes = []
                        else:
                            available_pages = sorted(list(filtered_data['page_name'].dropna().unique()))
                            if available_pages:
                                selected_pages = st.multiselect(
                                    "Include Pages",
                                    options=available_pages,
                                    default=available_pages[:10],  # Show top 10 by default
                                    help="Select specific pages to include in analysis"
                                )
                            else:
                                selected_pages = []
                        
                        # Device type filter for journeys
                        journey_device_filter = st.selectbox(
                            "Device Type Focus",
                            options=['All Devices'] + sorted(list(filtered_data['device_type'].unique())),
                            help="Analyze journeys for specific device types"
                        )
                
                # Apply journey-specific filters
                journey_filtered_data = filtered_data.copy()
                
                # App filter (from main controls)
                if selected_app_main != 'All Apps':
                    journey_filtered_data = journey_filtered_data[journey_filtered_data['app_name'] == selected_app_main]
                
                # Time filter
                if journey_time_filter == "Last 7 Days":
                    cutoff_date = pd.Timestamp.now().date() - pd.Timedelta(days=7)
                    journey_filtered_data = journey_filtered_data[journey_filtered_data['date'] >= cutoff_date]
                elif journey_time_filter == "Last 30 Days":
                    cutoff_date = pd.Timestamp.now().date() - pd.Timedelta(days=30)
                    journey_filtered_data = journey_filtered_data[journey_filtered_data['date'] >= cutoff_date]
                elif journey_time_filter == "Custom Range":
                    journey_filtered_data = journey_filtered_data[
                        (journey_filtered_data['date'] >= custom_start) &
                        (journey_filtered_data['date'] <= custom_end)
                    ]
                
                # Session duration filter
                if session_duration_filter:
                    journey_filtered_data = journey_filtered_data[
                        (journey_filtered_data['duration'] >= session_duration_filter[0]) &
                        (journey_filtered_data['duration'] <= session_duration_filter[1])
                    ]
                
                # Device filter
                if journey_device_filter != 'All Devices':
                    journey_filtered_data = journey_filtered_data[journey_filtered_data['device_type'] == journey_device_filter]
                
                # Page/Route filter
                if data_source == "Routes" and has_route_data and 'selected_routes' in locals():
                    if selected_routes:
                        route_mask = (
                            journey_filtered_data['route'].isin(selected_routes) |
                            journey_filtered_data['prev_route'].isin(selected_routes)
                        )
                        journey_filtered_data = journey_filtered_data[route_mask]
                elif 'selected_pages' in locals():
                    if selected_pages:
                        journey_filtered_data = journey_filtered_data[journey_filtered_data['page_name'].isin(selected_pages)]
                
                # Show filter impact with app-specific information
                if len(journey_filtered_data) != len(filtered_data) or selected_app_main != 'All Apps':
                    app_info = f" for {selected_app_main}" if selected_app_main != 'All Apps' else ""
                    st.info(f"🔍 Journey Analysis{app_info}: {len(journey_filtered_data):,} records ({journey_filtered_data['distinct_id'].nunique()} unique users)"
                           f"{f' filtered from {len(filtered_data):,} total records' if len(journey_filtered_data) != len(filtered_data) else ''}")
                
                # Update data source check with filtered data
                if data_source == "Routes":
                    has_route_data_filtered = len(journey_filtered_data[(journey_filtered_data['route'] != '') & (journey_filtered_data['prev_route'] != '')]) > 0
                else:
                    has_page_data_filtered = len(journey_filtered_data[journey_filtered_data['page_name'] != '']) > 0
                
                # Prepare journey data based on selected source (using filtered data)
                if data_source == "Routes" and has_route_data:
                    journey_data = journey_filtered_data[(journey_filtered_data['route'] != '') & (journey_filtered_data['prev_route'] != '')].copy()
                    source_col, target_col = 'prev_route', 'route'
                elif has_page_data:
                    # Create page transitions from timestamp sequences
                    page_data = journey_filtered_data[journey_filtered_data['page_name'] != ''].copy()
                    page_data = page_data.sort_values(['distinct_id', 'timestamp'])
                    
                    # Create prev_page column by shifting within each user
                    page_data['prev_page'] = page_data.groupby('distinct_id')['page_name'].shift(1)
                    journey_data = page_data[page_data['prev_page'].notna()].copy()
                    source_col, target_col = 'prev_page', 'page_name'
                else:
                    journey_data = pd.DataFrame()
                
                # Apply minimum journey length filter
                if not journey_data.empty and min_journey_length > 1:
                    # Count journey steps per user
                    user_journey_lengths = journey_data.groupby('distinct_id').size()
                    qualified_users = user_journey_lengths[user_journey_lengths >= min_journey_length].index
                    journey_data = journey_data[journey_data['distinct_id'].isin(qualified_users)]
                    
                    if len(qualified_users) < len(user_journey_lengths):
                        st.info(f"🚀 Journey Length Filter: {len(qualified_users)} users with {min_journey_length}+ steps (from {len(user_journey_lengths)} total)")
                
                # Apply active users filter
                if not journey_data.empty and active_users_only:
                    # Users with multiple different navigation actions
                    user_activity = journey_data.groupby('distinct_id').agg({
                        target_col: 'nunique',
                        'uuid': 'count'
                    })
                    active_user_threshold = 2  # At least 2 different pages/routes
                    active_users = user_activity[user_activity[target_col] >= active_user_threshold].index
                    journey_data = journey_data[journey_data['distinct_id'].isin(active_users)]
                    
                    if len(active_users) < len(user_activity):
                        st.info(f"🎯 Active Users Filter: {len(active_users)} active users (visited {active_user_threshold}+ different pages)")
                    
                if not journey_data.empty:
                    if analysis_type == "Navigation Flow Chart":
                        # Original bar chart analysis (enhanced)
                        flow_data = journey_data.groupby([source_col, target_col, 'app_name']).agg({
                            'distinct_id': 'nunique',
                            'uuid': 'count'
                        }).reset_index()
                        flow_data.columns = [source_col, target_col, 'app_name', 'unique_users', 'total_flows']
                        flow_data = flow_data.sort_values('total_flows', ascending=False).head(20)
                        flow_data['flow_path'] = flow_data[source_col] + ' → ' + flow_data[target_col]
                        
                        fig = px.bar(flow_data, 
                                    x='total_flows', 
                                    y='flow_path', 
                                    color='app_name',
                                    orientation='h',
                                    title=f'Top 20 Navigation Flows - {data_source}',
                                    labels={'total_flows': 'Total Transitions', 'flow_path': 'Navigation Path'},
                                    hover_data=['unique_users'])
                        fig.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            height=600
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif analysis_type == "Sankey Flow Diagram":
                        # Interactive Sankey diagram
                        flow_summary = journey_data.groupby([source_col, target_col]).agg({
                            'distinct_id': 'nunique'
                        }).reset_index()
                        flow_summary.columns = ['source', 'target', 'value']
                        
                        # Get top flows for readability - increase limit for more comprehensive view
                        max_flows = st.slider(
                            "Max Flows to Display", 
                            min_value=20, 
                            max_value=200, 
                            value=50,
                            help="Increase to see more navigation patterns (may slow down visualization)"
                        )
                        flow_summary = flow_summary.sort_values('value', ascending=False).head(max_flows)
                        
                        # Create unique node lists
                        all_nodes = list(set(flow_summary['source'].tolist() + flow_summary['target'].tolist()))
                        node_indices = {node: i for i, node in enumerate(all_nodes)}
                        
                        # Map to indices
                        flow_summary['source_idx'] = flow_summary['source'].map(node_indices)
                        flow_summary['target_idx'] = flow_summary['target'].map(node_indices)
                        
                        # Create Sankey diagram
                        fig = go.Figure(data=[go.Sankey(
                            node = dict(
                                pad = 15,
                                thickness = 20,
                                line = dict(color = "black", width = 0.5),
                                label = all_nodes,
                                color = "lightblue"
                            ),
                            link = dict(
                                source = flow_summary['source_idx'].tolist(),
                                target = flow_summary['target_idx'].tolist(),
                                value = flow_summary['value'].tolist()
                            )
                        )])
                        
                        fig.update_layout(
                            title_text=f"User Journey Flow - {data_source}",
                            font_size=10,
                            height=600
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Flow statistics
                        st.write("**Flow Statistics:**")
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        with col_stat1:
                            st.metric("Total Unique Paths", len(flow_summary))
                        with col_stat2:
                            st.metric("Total Users in Flows", flow_summary['value'].sum())
                        with col_stat3:
                            st.metric("Most Common Flow", flow_summary.iloc[0]['value'] if len(flow_summary) > 0 else 0)
                    
                    elif analysis_type == "User Path Analysis":
                        # Analyze complete user journeys
                        st.write("**Complete User Journey Analysis**")
                        
                        # Create user journey sequences
                        user_journeys = journey_data.groupby('distinct_id').apply(
                            lambda x: x.sort_values('timestamp')[target_col].tolist()
                        ).reset_index()
                        user_journeys.columns = ['user_id', 'journey_path']
                        user_journeys['journey_length'] = user_journeys['journey_path'].apply(len)
                        user_journeys['journey_string'] = user_journeys['journey_path'].apply(lambda x: ' → '.join(x))
                        
                        # Journey length distribution
                        length_dist = user_journeys['journey_length'].value_counts().sort_index()
                        fig = px.bar(x=length_dist.index, y=length_dist.values,
                                    title='User Journey Length Distribution',
                                    labels={'x': 'Journey Length (Pages)', 'y': 'Number of Users'})
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Most common journey patterns
                        common_patterns = user_journeys['journey_string'].value_counts().head(10)
                        st.write("**Top 10 Most Common Journey Patterns:**")
                        for i, (pattern, count) in enumerate(common_patterns.items(), 1):
                            st.write(f"{i}. **{pattern}** ({count} users)")
                    
                    elif analysis_type == "Drop-off Analysis":
                        # Analyze where users exit
                        st.write("**User Drop-off Point Analysis**")
                        
                        # Calculate exit rates for each page
                        page_entries = journey_data[source_col].value_counts()
                        page_exits = journey_data[target_col].value_counts()
                        
                        # Pages where users typically end their journey
                        exit_analysis = pd.DataFrame({
                            'page': page_exits.index,
                            'visits': page_exits.values
                        })
                        
                        # Calculate bounce rate (approximate)
                        total_visits = journey_data.groupby(target_col)['distinct_id'].nunique()
                        continuing_users = journey_data.groupby(source_col)['distinct_id'].nunique()
                        
                        bounce_data = pd.DataFrame({
                            'page': total_visits.index,
                            'total_visits': total_visits.values
                        })
                        
                        bounce_data['continuing_visits'] = bounce_data['page'].map(continuing_users).fillna(0)
                        bounce_data['bounce_rate'] = (1 - bounce_data['continuing_visits'] / bounce_data['total_visits']) * 100
                        bounce_data = bounce_data.sort_values('bounce_rate', ascending=False).head(15)
                        
                        fig = px.bar(bounce_data, x='page', y='bounce_rate',
                                    title='Page Bounce Rates (Where Users Stop)',
                                    labels={'bounce_rate': 'Bounce Rate (%)', 'page': 'Page/Route'})
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.write("**High Bounce Rate Pages:**")
                        for i, row in bounce_data.head(5).iterrows():
                            st.write(f"• **{row['page']}**: {row['bounce_rate']:.1f}% bounce rate ({row['total_visits']} visits)")
                
                else:
                    st.info(f"No {data_source.lower()} transition data available in current selection")
            else:
                st.info("No navigation data available in current selection. Need either route transitions or page name data.")
    
    with tab4:
        st.header("⚡ Technical Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Device Performance by App
            device_perf = filtered_data.groupby(['device_type', 'app_name']).agg({
                'duration': 'mean',
                'distinct_id': 'nunique'
            }).reset_index()
            
            fig = px.bar(device_perf, x='device_type', y='duration', color='app_name',
                        title='Average Session Duration by Device Type & App',
                        labels={'duration': 'Average Duration (s)', 'device_type': 'Device Type'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Geographic Performance by App - Multiple visualization options
            geo_viz_type = st.selectbox(
                "Geographic Visualization Type",
                ["Treemap", "Bar Chart", "Scatter Plot", "Heatmap"],
                help="Choose the best visualization for geographic performance data",
                key="geo_viz_selector"
            )
            
            geo_perf = filtered_data.groupby(['country', 'app_name']).agg({
                'duration': 'mean',
                'distinct_id': 'nunique'
            }).reset_index()
            
            # Get top countries by total users
            top_countries = filtered_data.groupby('country')['distinct_id'].nunique().sort_values(ascending=False).head(15).index
            geo_perf_filtered = geo_perf[geo_perf['country'].isin(top_countries)]
            
            if geo_viz_type == "Treemap":
                # Treemap - Great for hierarchical data with size representation
                fig = px.treemap(geo_perf_filtered, 
                                path=['country', 'app_name'], 
                                values='distinct_id',
                                color='duration',
                                color_continuous_scale='RdYlBu_r',
                                title='User Distribution & Performance by Country & App',
                                hover_data=['duration'])
                
            elif geo_viz_type == "Heatmap":
                # Pivot for heatmap
                heatmap_data = geo_perf_filtered.pivot(index='country', columns='app_name', values='duration').fillna(0)
                fig = px.imshow(heatmap_data,
                               title='Performance Heatmap: Duration by Country & App',
                               labels={'color': 'Avg Duration (s)'})
                
            elif geo_viz_type == "Bar Chart":
                # Horizontal bar chart - easier to read country names
                fig = px.bar(geo_perf_filtered.head(20), 
                            y='country', x='distinct_id', 
                            color='app_name',
                            orientation='h',
                            title='Top Countries by User Count & App',
                            labels={'distinct_id': 'Number of Users', 'country': 'Country'})
                
            else:  # Scatter Plot (original)
                fig = px.scatter(geo_perf_filtered, x='distinct_id', y='duration', 
                               color='app_name', size='distinct_id',
                               hover_data=['country'],
                               title='Performance Scatter: Users vs Duration by Country',
                               labels={'distinct_id': 'Number of Users', 'duration': 'Average Duration (s)'})
                fig.update_traces(marker=dict(sizemin=8, sizemode='diameter'))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Debug info for geographic data
            countries_available = filtered_data['country'].nunique()
            st.caption(f"ℹ️ {countries_available} countries in data, showing top performers")
        
        # GPS Coordinates Map
        if 'latitude' in filtered_data.columns and filtered_data['latitude'].notna().any():
            st.subheader("🗺️ User Location Map")
            
            # Filter out rows without GPS coordinates
            map_data = filtered_data[
                (filtered_data['latitude'].notna()) & 
                (filtered_data['longitude'].notna())
            ].copy()
            
            if len(map_data) > 0:
                # Create location summary for map
                location_summary = map_data.groupby(['app_name', 'latitude', 'longitude', 'location']).agg({
                    'distinct_id': 'nunique',
                    'uuid': 'count'
                }).reset_index().rename(columns={
                    'distinct_id': 'users',
                    'uuid': 'events'
                })
                
                # Create map
                fig = px.scatter_mapbox(
                    location_summary,
                    lat='latitude',
                    lon='longitude',
                    size='users',
                    color='app_name',
                    hover_data=['location', 'users', 'events'],
                    zoom=4,
                    height=500,
                    title='User Activity by Geographic Location & App'
                )
                
                # Use OpenStreetMap for the map
                fig.update_layout(mapbox_style="open-street-map")
                fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Location statistics
                col_stats1, col_stats2 = st.columns(2)
                with col_stats1:
                    st.metric("📍 Unique Locations", len(location_summary))
                with col_stats2:
                    if selected_country != 'All Countries':
                        country_locations = location_summary[
                            location_summary['location'].str.contains(selected_country, na=False)
                        ]
                        country_flag = "🇮🇩" if selected_country == "Indonesia" else "🌍"
                        st.metric(f"{country_flag} {selected_country} Locations", len(country_locations))
                    else:
                        all_countries = location_summary['location'].str.extract(r', ([^,]+)$')[0].value_counts()
                        st.metric("🌍 Countries Represented", len(all_countries))
            else:
                st.info("No GPS coordinate data available for the current filters")
        
        # Additional performance metrics
        col3, col4 = st.columns(2)
        
        with col3:
            # OS Performance by App
            os_perf = filtered_data.groupby(['os', 'app_name']).agg({
                'duration': 'mean',
                'distinct_id': 'nunique'
            }).reset_index()
            
            # Better handling of OS data
            os_perf_clean = os_perf[os_perf['os'] != 'Unknown'].copy()
            
            if len(os_perf_clean) > 0:
                # Show top 8 OS for better visualization
                top_os = os_perf_clean.groupby('os')['distinct_id'].sum().sort_values(ascending=False).head(8).index
                os_perf_filtered = os_perf_clean[os_perf_clean['os'].isin(top_os)]
                
                fig = px.bar(os_perf_filtered, x='os', y='duration', color='app_name',
                            title='Average Duration by Operating System & App',
                            labels={'duration': 'Average Duration (s)', 'os': 'Operating System'})
                fig.update_layout(xaxis_tickangle=-45)
            else:
                # Fallback: Include Unknown OS if that's all we have
                fig = px.bar(os_perf, x='os', y='duration', color='app_name',
                            title='Average Duration by Operating System & App (Including Unknown)',
                            labels={'duration': 'Average Duration (s)', 'os': 'Operating System'})
                fig.update_layout(xaxis_tickangle=-45)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Debug info for OS data
            known_os_records = len(filtered_data[filtered_data['os'] != 'Unknown'])
            st.caption(f"ℹ️ Known OS data: {known_os_records}/{len(filtered_data)} records ({known_os_records/len(filtered_data)*100:.1f}%)")
        
        with col4:
            # App Version Performance - Multiple visualization options
            version_viz_type = st.selectbox(
                "Version Visualization Type",
                ["Sunburst", "Bar Chart", "Treemap", "Simple App Comparison"],
                help="Choose the best visualization for version data",
                key="version_viz_selector"
            )
            
            version_data = filtered_data.copy()
            version_data['app_version'] = version_data['app_version'].fillna('Unknown')
            version_data['app_version'] = version_data['app_version'].replace('', 'Unknown')
            
            # Check if we have meaningful version data
            version_counts = version_data[version_data['app_version'] != 'Unknown']['app_version'].nunique()
            
            if version_counts > 0 and version_viz_type != "Simple App Comparison":
                # Use actual version data
                version_perf = version_data.groupby(['app_name', 'app_version']).agg({
                    'duration': 'mean',
                    'distinct_id': 'nunique'
                }).reset_index()
                
                # Show top versions only for readability
                top_versions = version_data['app_version'].value_counts().head(12).index
                version_perf = version_perf[version_perf['app_version'].isin(top_versions)]
                
                if version_viz_type == "Sunburst":
                    # Sunburst - Great for hierarchical app -> version relationships
                    fig = px.sunburst(version_perf, 
                                     path=['app_name', 'app_version'], 
                                     values='distinct_id',
                                     color='duration',
                                     title='App Versions: Hierarchy & Performance')
                    
                elif version_viz_type == "Treemap":
                    # Treemap - Shows proportion and performance
                    fig = px.treemap(version_perf, 
                                    path=['app_name', 'app_version'], 
                                    values='distinct_id',
                                    color='duration',
                                    color_continuous_scale='RdYlGn_r',
                                    title='App Version Usage & Performance')
                    
                else:  # Bar Chart
                    fig = px.bar(version_perf, x='app_name', y='duration', color='app_version',
                                title='Average Duration by App Version',
                                labels={'duration': 'Average Duration (s)', 'app_name': 'Application'})
            else:
                # Fallback: Show by app only
                app_perf = version_data.groupby('app_name').agg({
                    'duration': 'mean',
                    'distinct_id': 'nunique'
                }).reset_index()
                
                if version_viz_type == "Simple App Comparison":
                    # Enhanced app comparison
                    fig = px.bar(app_perf, x='app_name', y='duration',
                                color='distinct_id',
                                title='App Performance Comparison',
                                labels={'duration': 'Average Duration (s)', 'app_name': 'Application',
                                       'color': 'User Count'},
                                text='distinct_id')
                    fig.update_traces(texttemplate='%{text} users', textposition='outside')
                else:
                    fig = px.bar(app_perf, x='app_name', y='duration',
                                title='Average Duration by Application (No Version Data Available)',
                                labels={'duration': 'Average Duration (s)', 'app_name': 'Application'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Debug info for version data
            version_available = len(filtered_data[filtered_data['app_version'] != ''])
            st.caption(f"ℹ️ Version data available for {version_available}/{len(filtered_data)} records ({version_available/len(filtered_data)*100:.1f}%)")
        
        # Performance comparison table
        st.subheader("📊 Performance Metrics by App")
        perf_summary = filtered_data.groupby('app_name').agg({
            'duration': ['mean', 'median', 'std'],
            'distinct_id': 'nunique',
            'session_id': 'nunique'
        }).round(2)
        
        # Flatten column names
        perf_summary.columns = ['Avg Duration', 'Median Duration', 'Duration StdDev', 'Users', 'Sessions']
        perf_summary = perf_summary.reset_index()
        st.dataframe(perf_summary, use_container_width=True)
        
        # Data Table - All Users from All Apps
        st.subheader("📋 Raw Data Sample - All Users from All Apps")
        
        # Show data size info
        total_users = filtered_data['distinct_id'].nunique()
        total_records = len(filtered_data)
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("👥 Total Users", f"{total_users:,}")
        with col_info2:
            st.metric("📊 Total Records", f"{total_records:,}")
        with col_info3:
            apps_count = filtered_data['app_name'].nunique()
            st.metric("🏢 Apps", f"{apps_count}")
        
        # Search filter
        st.subheader("🔍 Search & Filter Options")
        
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            # Text search across multiple fields
            search_text = st.text_input(
                "Search in data", 
                placeholder="Enter user ID, page name, widget name, etc.",
                help="Search across user IDs, page names, widget names, and events"
            )
            
        with search_col2:
            # Event type filter
            available_events = ['All Events'] + sorted(list(filtered_data['event'].unique()))
            selected_event = st.selectbox(
                "Event Type Filter",
                options=available_events,
                help="Filter by specific event types"
            )
        
        # Additional filters in expandable section
        with st.expander("🎛️ Advanced Search Filters"):
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                # User-specific filter
                user_search = st.text_input(
                    "Specific User ID",
                    placeholder="Enter exact user email/ID",
                    help="Filter to show data for a specific user"
                )
                
                # Page/Widget filter
                page_widget_search = st.text_input(
                    "Page/Widget Contains",
                    placeholder="Enter page or widget name",
                    help="Filter by page name or widget name content"
                )
            
            with filter_col2:
                # Duration range filter
                if filtered_data['duration'].notna().any():
                    min_duration = int(filtered_data['duration'].min()) if filtered_data['duration'].min() >= 0 else 0
                    max_duration = int(filtered_data['duration'].max()) if filtered_data['duration'].max() > 0 else 100
                    
                    if max_duration > min_duration:
                        duration_range = st.slider(
                            "Duration Range (seconds)",
                            min_value=min_duration,
                            max_value=max_duration,
                            value=(min_duration, max_duration),
                            help="Filter by session duration"
                        )
                    else:
                        duration_range = None
                else:
                    duration_range = None
                
                # Show only users with widgets/interactions
                show_interactive_only = st.checkbox(
                    "Interactive Users Only",
                    help="Show only users with widget interactions or page navigations"
                )
        
        # Apply search filters
        search_filtered_data = filtered_data.copy()
        
        if search_text:
            # Search across multiple columns
            search_cols = ['distinct_id', 'page_name', 'widget_name', 'event', 'country', 'location']
            search_mask = pd.Series([False] * len(search_filtered_data))
            
            for col in search_cols:
                if col in search_filtered_data.columns:
                    search_mask |= search_filtered_data[col].astype(str).str.contains(
                        search_text, case=False, na=False
                    )
            search_filtered_data = search_filtered_data[search_mask]
        
        if selected_event != 'All Events':
            search_filtered_data = search_filtered_data[search_filtered_data['event'] == selected_event]
        
        if user_search:
            search_filtered_data = search_filtered_data[
                search_filtered_data['distinct_id'].str.contains(user_search, case=False, na=False)
            ]
        
        if page_widget_search:
            page_widget_mask = (
                search_filtered_data['page_name'].str.contains(page_widget_search, case=False, na=False) |
                search_filtered_data['widget_name'].str.contains(page_widget_search, case=False, na=False)
            )
            search_filtered_data = search_filtered_data[page_widget_mask]
        
        if duration_range and 'duration' in search_filtered_data.columns:
            search_filtered_data = search_filtered_data[
                (search_filtered_data['duration'] >= duration_range[0]) &
                (search_filtered_data['duration'] <= duration_range[1])
            ]
        
        if show_interactive_only:
            interactive_mask = (
                (search_filtered_data['widget_name'].notna() & (search_filtered_data['widget_name'] != '')) |
                (search_filtered_data['page_name'].notna() & (search_filtered_data['page_name'] != ''))
            )
            search_filtered_data = search_filtered_data[interactive_mask]
        
        # Update metrics with search results
        if len(search_filtered_data) != len(filtered_data):
            st.info(f"🔍 Search Results: {len(search_filtered_data):,} records found (filtered from {len(filtered_data):,})")
        
        # Select columns to display
        display_columns = ['app_name', 'distinct_id', 'event', 'timestamp', 'duration', 
                          'page_name', 'widget_name', 'device_type', 'os', 'country', 'location']
        
        # Filter to only existing columns
        available_columns = [col for col in display_columns if col in search_filtered_data.columns]
        
        # Option to limit display for performance
        show_all = st.checkbox("Show all records (may be slow for large datasets)", value=False)
        
        if show_all:
            display_data = search_filtered_data[available_columns]
            st.info(f"Displaying all {len(display_data):,} records")
        else:
            # Show a larger sample but not everything
            sample_size = min(5000, len(search_filtered_data))
            display_data = search_filtered_data[available_columns].head(sample_size)
            st.info(f"Displaying first {len(display_data):,} records. Check 'Show all records' to see all data.")
        
        # Sort by app_name and timestamp for better organization
        if 'timestamp' in display_data.columns:
            display_data = display_data.sort_values(['app_name', 'timestamp'], ascending=[True, False])
        
        st.dataframe(display_data, use_container_width=True, height=400)
        
        # User breakdown by app (based on search results)
        st.subheader("👥 User Distribution by App")
        user_breakdown = search_filtered_data.groupby('app_name').agg({
            'distinct_id': 'nunique',
            'uuid': 'count'
        }).reset_index()
        user_breakdown.columns = ['App', 'Unique Users', 'Total Events']
        user_breakdown = user_breakdown.sort_values('Unique Users', ascending=False)
        
        # Show as both table and chart
        col_table, col_chart = st.columns([1, 1])
        
        with col_table:
            st.dataframe(user_breakdown, use_container_width=True, hide_index=True)
        
        with col_chart:
            fig = px.bar(user_breakdown, x='App', y='Unique Users', 
                        title='Unique Users by App',
                        color='App')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        st.header("🚀 Advanced Usage Analytics")
        st.markdown("*Based on comprehensive usability research - measuring genuine app usage and user learning patterns*")
        
        # Overview metrics for all apps
        st.subheader("📊 All Apps Overview Comparison")
        overview_metrics = filtered_data.groupby('app_name').agg({
            'distinct_id': 'nunique',
            'duration': 'mean',
            'widget_name': lambda x: len([w for w in x if w != '']),
            'tab_name': lambda x: len([t for t in x if t != '']),
            'session_id': 'nunique',
            'checkin': lambda x: len([c for c in x if c != '']),
            'checkout': lambda x: len([c for c in x if c != ''])
        }).reset_index()
        
        overview_metrics.columns = ['App', 'Users', 'Avg Duration', 'Widget Uses', 'Tab Uses', 'Sessions', 'CheckIns', 'CheckOuts']
        overview_metrics['Completion Rate'] = (overview_metrics['CheckOuts'] / overview_metrics['CheckIns'] * 100).round(2)
        overview_metrics['Widget Rate'] = (overview_metrics['Widget Uses'] / overview_metrics['Users']).round(2)
        
        # Display as a nice table
        st.dataframe(overview_metrics[['App', 'Users', 'Avg Duration', 'Sessions', 'Widget Rate', 'Completion Rate']], use_container_width=True)
        
        # Quick comparison charts
        col_overview1, col_overview2 = st.columns(2)
        
        with col_overview1:
            fig = px.bar(overview_metrics, x='App', y='Users', color='App',
                        title='Total Users by App')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_overview2:
            fig = px.bar(overview_metrics, x='App', y='Widget Rate', color='App',
                        title='Widget Interactions per User by App')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # 1. Progressive Usage Indicators
        st.subheader("📈 Progressive Usage Indicators")
        col1, col2 = st.columns(2)
        
        with col1:
            # User Maturity Levels based on the article
            user_sessions = filtered_data.groupby('distinct_id').agg({
                'duration': 'mean',
                'tab_name': lambda x: len([t for t in x if t != '']),
                'widget_name': lambda x: len([w for w in x if w != '']),
                'session_id': 'nunique'
            }).reset_index()
            
            # Classify users based on article criteria
            def classify_user_maturity(row):
                avg_duration = row['duration']
                tab_count = row['tab_name']
                widget_count = row['widget_name']
                sessions = row['session_id']
                
                if avg_duration < 30 or (tab_count <= 1 and widget_count == 0):
                    return 'New/Struggling'
                elif 30 <= avg_duration <= 120 and 1 <= tab_count <= 2:
                    return 'Beginner'
                elif 120 <= avg_duration <= 300 and 3 <= tab_count <= 5:
                    return 'Intermediate'
                elif avg_duration > 300 and tab_count > 5:
                    return 'Advanced'
                elif sessions > 5 and widget_count > 10:
                    return 'Power User'
                else:
                    return 'Developing'
            
            user_sessions['maturity_level'] = user_sessions.apply(classify_user_maturity, axis=1)
            maturity_dist = user_sessions['maturity_level'].value_counts()
            
            fig = px.pie(values=maturity_dist.values, names=maturity_dist.index,
                        title='User Maturity Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Feature Adoption Rate per App - Ensure all apps are visible
            feature_adoption = filtered_data.groupby('app_name').agg({
                'distinct_id': 'nunique',
                'widget_name': lambda x: len([w for w in x if w != ''])
            }).reset_index()
            feature_adoption['adoption_rate'] = (feature_adoption['widget_name'] / feature_adoption['distinct_id'] * 100).round(2)
            
            # Ensure all filtered apps appear
            all_apps = pd.DataFrame({'app_name': filtered_data['app_name'].unique()})
            feature_adoption_full = all_apps.merge(feature_adoption, on='app_name', how='left')
            feature_adoption_full['adoption_rate'] = feature_adoption_full['adoption_rate'].fillna(0)
            
            fig = px.bar(feature_adoption_full, x='app_name', y='adoption_rate', color='app_name',
                        title='Feature Adoption Rate by App (%)',
                        labels={'adoption_rate': 'Widget Interactions per User (%)'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # 2. Session Quality Metrics
        st.subheader("✨ Session Quality Analysis")
        col3, col4 = st.columns(2)
        
        with col3:
            # Session Quality Classification
            def classify_session_quality(row):
                duration = row['duration']
                has_widget = row['widget_name'] != ''
                has_tab = row['tab_name'] != ''
                has_checkout = row['checkout'] != ''
                
                if duration > 180 and has_widget and has_tab and has_checkout:
                    return 'High Quality'
                elif duration > 60 and (has_widget or has_tab):
                    return 'Medium Quality'
                elif duration < 30 or (not has_widget and not has_tab):
                    return 'Low Quality'
                else:
                    return 'Basic Quality'
            
            filtered_data['session_quality'] = filtered_data.apply(classify_session_quality, axis=1)
            quality_by_app = filtered_data.groupby(['app_name', 'session_quality']).size().reset_index(name='count')
            
            fig = px.bar(quality_by_app, x='app_name', y='count', color='session_quality',
                        title='Session Quality Distribution by App',
                        labels={'count': 'Number of Sessions'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # App Usage Depth Analysis  
            usage_depth = filtered_data.groupby('app_name').agg({
                'distinct_id': 'nunique',
                'session_id': 'nunique', 
                'duration': 'mean',
                'widget_name': lambda x: len([w for w in x if w != '']),
                'tab_name': lambda x: len([t for t in x if t != ''])
            }).reset_index()
            
            usage_depth['widget_interactions_per_user'] = (usage_depth['widget_name'] / usage_depth['distinct_id']).round(2)
            usage_depth['tab_interactions_per_user'] = (usage_depth['tab_name'] / usage_depth['distinct_id']).round(2)
            
            fig = px.bar(usage_depth, x='app_name', y='widget_interactions_per_user', color='app_name',
                        title='Widget Interactions per User by App',
                        labels={'widget_interactions_per_user': 'Avg Widget Interactions per User'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # 3. Navigation Flow Analysis
        st.subheader("🧭 User Journey & Navigation Flow")
        col5, col6 = st.columns(2)
        
        with col5:
            # Tab Exploration Patterns by App
            tab_exploration = filtered_data[filtered_data['tab_name'] != ''].groupby(['distinct_id', 'app_name'])['tab_name'].apply(
                lambda x: len(set(x))
            ).reset_index()
            tab_exploration.columns = ['user', 'app_name', 'unique_tabs']
            
            if len(tab_exploration) > 0:
                fig = px.histogram(tab_exploration, x='unique_tabs', color='app_name', nbins=15,
                                 title='Tab Exploration Distribution by App',
                                 labels={'unique_tabs': 'Number of Unique Tabs Used', 'count': 'Number of Users'})
                fig.update_layout(barmode='overlay')
                fig.update_traces(opacity=0.7)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tab exploration data available")
        
        with col6:
            # App Navigation Depth Comparison
            nav_depth = filtered_data.groupby('app_name').agg({
                'page_name': lambda x: len(set([p for p in x if p != ''])),
                'tab_name': lambda x: len(set([t for t in x if t != ''])),
                'distinct_id': 'nunique'
            }).reset_index()
            nav_depth.columns = ['App', 'Unique Pages', 'Unique Tabs', 'Users']
            
            # Calculate depth per user
            nav_depth['Pages per User'] = (nav_depth['Unique Pages'] / nav_depth['Users']).round(2)
            nav_depth['Tabs per User'] = (nav_depth['Unique Tabs'] / nav_depth['Users']).round(2)
            
            fig = px.bar(nav_depth, x='App', y=['Pages per User', 'Tabs per User'],
                        title='Navigation Depth by App',
                        labels={'value': 'Average per User', 'variable': 'Navigation Type'})
            st.plotly_chart(fig, use_container_width=True)
        
        # 4. Learning Curve Analysis
        st.subheader("📚 User Learning Curve Analysis")
        col7, col8 = st.columns(2)
        
        with col7:
            # Session progression over time by App
            user_progression = filtered_data.groupby(['distinct_id', 'app_name', 'date']).agg({
                'duration': 'mean',
                'tab_name': lambda x: len(set([t for t in x if t != ''])),
                'widget_name': lambda x: len([w for w in x if w != ''])
            }).reset_index()
            
            # Calculate session number for each user within each app
            user_progression = user_progression.sort_values(['distinct_id', 'app_name', 'date'])
            user_progression['session_number'] = user_progression.groupby(['distinct_id', 'app_name']).cumcount() + 1
            
            # Average by session number and app
            avg_progression = user_progression.groupby(['session_number', 'app_name']).agg({
                'duration': 'mean',
                'tab_name': 'mean',
                'widget_name': 'mean'
            }).reset_index()
            
            # Only show first 10 sessions for clarity
            avg_progression_limited = avg_progression[avg_progression['session_number'] <= 10]
            
            fig = px.line(avg_progression_limited, x='session_number', y='duration', color='app_name',
                         title='Learning Curve: Average Duration by Session Number & App',
                         labels={'session_number': 'Session Number', 'duration': 'Average Duration (seconds)'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col8:
            # Feature Discovery Over Sessions by App
            feature_discovery = avg_progression[avg_progression['session_number'] <= 10]
            
            fig = px.line(feature_discovery, x='session_number', y='widget_name', color='app_name',
                         title='Feature Discovery: Widget Usage by Session & App',
                         labels={'session_number': 'Session Number', 'widget_name': 'Average Widgets Used'})
            st.plotly_chart(fig, use_container_width=True)
        
        # 5. Usability Problem Detection
        st.subheader("🚨 Usability Problem Detection")
        
        # Comprehensive usability analysis per app
        col9, col10 = st.columns(2)
        
        with col9:
            # App Engagement Quality Comparison
            engagement_quality = filtered_data.groupby('app_name').agg({
                'duration': ['mean', 'median'],
                'widget_name': lambda x: len([w for w in x if w != '']),
                'tab_name': lambda x: len([t for t in x if t != '']),
                'distinct_id': 'nunique'
            }).round(2)
            
            # Flatten column names
            engagement_quality.columns = ['Avg Duration', 'Median Duration', 'Total Widgets', 'Total Tabs', 'Users']
            engagement_quality = engagement_quality.reset_index()
            
            # Calculate engagement score
            engagement_quality['Widget Engagement Rate'] = (engagement_quality['Total Widgets'] / engagement_quality['Users']).round(2)
            engagement_quality['Tab Engagement Rate'] = (engagement_quality['Total Tabs'] / engagement_quality['Users']).round(2)
            
            fig = px.scatter(engagement_quality, 
                           x='Widget Engagement Rate', 
                           y='Avg Duration', 
                           size='Users',
                           color='app_name',
                           title='App Engagement Quality Matrix',
                           labels={'Widget Engagement Rate': 'Widget Interactions per User', 'Avg Duration': 'Average Session Duration (s)'},
                           hover_data=['Tab Engagement Rate'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col10:
            # Feature Usage Health by App
            feature_health = filtered_data.groupby('app_name').agg({
                'widget_name': [lambda x: len([w for w in x if w != '']), lambda x: len(set([w for w in x if w != '']))],
                'tab_name': [lambda x: len([t for t in x if t != '']), lambda x: len(set([t for t in x if t != '']))],
                'distinct_id': 'nunique'
            })
            
            # Flatten column names
            feature_health.columns = ['Widget Uses', 'Unique Widgets', 'Tab Uses', 'Unique Tabs', 'Users']
            feature_health = feature_health.reset_index()
            
            # Calculate diversity scores
            feature_health['Widget Diversity'] = (feature_health['Unique Widgets'] / feature_health['Widget Uses'] * 100).fillna(0).round(1)
            feature_health['Tab Diversity'] = (feature_health['Unique Tabs'] / feature_health['Tab Uses'] * 100).fillna(0).round(1)
            
            fig = px.bar(feature_health, 
                        x='app_name', 
                        y=['Widget Diversity', 'Tab Diversity'],
                        title='Feature Diversity Health by App (%)',
                        labels={'value': 'Diversity Score (%)', 'variable': 'Feature Type'})
            st.plotly_chart(fig, use_container_width=True)
        
        # App-specific usability insights table
        st.subheader("📊 App Usability Summary")
        usability_summary = filtered_data.groupby('app_name').agg({
            'distinct_id': 'nunique',
            'duration': 'mean',
            'widget_name': lambda x: len([w for w in x if w != '']),
            'tab_name': lambda x: len([t for t in x if t != '']),
            'page_name': lambda x: len(set([p for p in x if p != '']))
        }).round(2)
        
        usability_summary.columns = ['Users', 'Avg Duration', 'Widget Interactions', 'Tab Interactions', 'Unique Pages']
        usability_summary['Widgets per User'] = (usability_summary['Widget Interactions'] / usability_summary['Users']).round(2)
        usability_summary['Tabs per User'] = (usability_summary['Tab Interactions'] / usability_summary['Users']).round(2)
        usability_summary = usability_summary.reset_index()
        
        st.dataframe(usability_summary[['app_name', 'Users', 'Avg Duration', 'Widgets per User', 'Tabs per User', 'Unique Pages']], use_container_width=True)
    
    return data, filtered_data

if __name__ == "__main__":
    main()