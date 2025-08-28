# Additional callbacks for the dashboard
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from dash import Input, Output, callback

def register_additional_callbacks(app, data, filter_data):
    """Register all additional callbacks for the dashboard"""
    
    # Session Duration Distribution
    @callback(
        Output('session-duration-dist', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_session_duration_dist(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Filter out invalid durations and create meaningful bins
        valid_durations = filtered_data[filtered_data['duration'] >= 0]['duration']
        
        if valid_durations.empty:
            fig = go.Figure()
            fig.add_annotation(text="No valid session duration data", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Session Duration Distribution')
            return fig
        
        # Create custom bins for better visualization
        max_duration = min(valid_durations.max(), 600)  # Cap at 10 minutes for better visualization
        bins = [0, 10, 30, 60, 120, 300, max_duration]
        bin_labels = ['0-10s', '10-30s', '30s-1min', '1-2min', '2-5min', '5min+']
        
        # Manually bin the data
        binned_data = []
        for i in range(len(bins)-1):
            count = len(valid_durations[(valid_durations >= bins[i]) & (valid_durations < bins[i+1])])
            binned_data.append({'duration_bin': bin_labels[i], 'count': count})
        
        bin_df = pd.DataFrame(binned_data)
        
        fig = px.bar(bin_df, x='duration_bin', y='count',
                     title='Session Duration Distribution',
                     labels={'duration_bin': 'Duration Range', 'count': 'Number of Sessions'})
        
        fig.add_vline(x=1.5, line_dash="dash", line_color="red", 
                     annotation_text="Bounce Threshold")
        
        return fig
    
    # Feature Usage
    @callback(
        Output('feature-usage', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_feature_usage(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Get widget usage - use Widget_Name from extracted properties
        widget_usage = filtered_data[filtered_data['widget_name'] != ''].groupby('widget_name').size().reset_index(name='count')
        widget_usage = widget_usage.sort_values('count', ascending=False).head(15)  # Changed to descending and head for top items
        
        if widget_usage.empty:
            fig = go.Figure()
            fig.add_annotation(text="No widget data available for selected filters", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Top 15 Most Used Features/Widgets')
        else:
            fig = px.bar(widget_usage, x='widget_name', y='count',
                         title='Top 15 Most Used Features/Widgets',
                         labels={'count': 'Usage Count', 'widget_name': 'Widget/Feature'})
            fig.update_xaxes(tickangle=45)
        
        return fig
    
    # Platform Breakdown
    @callback(
        Output('platform-breakdown', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_platform_breakdown(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Get top 3 OS and Device Types
        os_dist = filtered_data['os'].value_counts().head(3).reset_index()
        os_dist.columns = ['platform', 'count']
        os_dist['type'] = 'Operating System'
        
        device_dist = filtered_data['device_type'].value_counts().head(3).reset_index()  
        device_dist.columns = ['platform', 'count']
        device_dist['type'] = 'Device Type'
        
        # Combine data
        platform_data = pd.concat([os_dist, device_dist], ignore_index=True)
        
        if platform_data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No platform data available", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title="Top 3 Platforms by Type")
        else:
            fig = px.bar(platform_data, x='platform', y='count', color='type', barmode='group',
                         title='Top 3 Operating Systems and Device Types',
                         labels={'count': 'Number of Users', 'platform': 'Platform'})
            fig.update_xaxes(tickangle=45)
        
        return fig
    
    # Network Analysis
    @callback(
        Output('network-analysis', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_network_analysis(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Network type usage
        network_data = []
        for _, row in filtered_data.iterrows():
            if row['network_wifi'] == True:
                network_data.append('WiFi')
            elif row['network_wifi'] == False:
                network_data.append('Cellular')
            else:
                network_data.append('Unknown')
        
        network_df = pd.DataFrame({'network_type': network_data, 'app_name': filtered_data['app_name']})
        network_counts = network_df.groupby(['app_name', 'network_type']).size().reset_index(name='count')
        
        fig = px.bar(network_counts, x='app_name', y='count', color='network_type',
                     title='Network Usage by App',
                     labels={'count': 'Number of Sessions', 'app_name': 'Application'})
        
        return fig
    
    # Hourly Usage Pattern
    @callback(
        Output('hourly-usage', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_hourly_usage(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Extract hour from timestamp
        filtered_data['hour'] = filtered_data['timestamp'].dt.hour
        filtered_data['day_of_week'] = filtered_data['timestamp'].dt.day_name()
        
        # Create heatmap data
        heatmap_data = filtered_data.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex(day_order)
        
        fig = px.imshow(heatmap_pivot, 
                       title='Usage Heatmap (Hour vs Day of Week)',
                       labels=dict(x="Hour of Day", y="Day of Week", color="Activity Count"),
                       aspect="auto")
        
        return fig
    
    # User Engagement Quality
    @callback(
        Output('engagement-scatter', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_engagement_scatter(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Define engagement categories based on duration and activity
        engagement_data = []
        for app in app_names:
            app_data = filtered_data[filtered_data['app_name'] == app]
            if len(app_data) == 0:
                continue
                
            # Categorize users by engagement level
            high_engagement = len(app_data[app_data['duration'] >= 120])  # 2+ minutes
            medium_engagement = len(app_data[(app_data['duration'] >= 30) & (app_data['duration'] < 120)])  # 30s-2min
            low_engagement = len(app_data[app_data['duration'] < 30])  # <30s
            
            total = high_engagement + medium_engagement + low_engagement
            if total > 0:
                engagement_data.extend([
                    {'app': app, 'engagement': 'High (2+ min)', 'users': high_engagement, 'percentage': high_engagement/total*100},
                    {'app': app, 'engagement': 'Medium (30s-2min)', 'users': medium_engagement, 'percentage': medium_engagement/total*100},
                    {'app': app, 'engagement': 'Low (<30s)', 'users': low_engagement, 'percentage': low_engagement/total*100}
                ])
        
        if not engagement_data:
            fig = go.Figure()
            fig.add_annotation(text="No engagement data available", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='User Engagement Quality by App')
            return fig
        
        engagement_df = pd.DataFrame(engagement_data)
        
        fig = px.bar(engagement_df, x='app', y='percentage', color='engagement',
                     title='User Engagement Quality by App',
                     labels={'percentage': 'Percentage of Users', 'app': 'Application'},
                     color_discrete_map={'High (2+ min)': 'green', 'Medium (30s-2min)': 'orange', 'Low (<30s)': 'red'})
        
        return fig
    
    # Screen Popularity
    @callback(
        Output('screen-popularity', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_screen_popularity(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Screen usage
        screen_usage = filtered_data[filtered_data['screen_name'] != ''].groupby(['app_name', 'screen_name']).size().reset_index(name='count')
        screen_usage = screen_usage.sort_values('count', ascending=False).head(20)
        
        if screen_usage.empty:
            fig = go.Figure()
            fig.add_annotation(text="No screen data available for selected filters", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Screen Popularity Across Apps')
        else:
            fig = px.treemap(screen_usage, path=['app_name', 'screen_name'], values='count',
                            title='Screen Popularity Across Apps')
        
        return fig
    
    # User Journey (Top Paths)
    @callback(
        Output('user-journey', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_user_journey(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Analyze user flow and drop-off points
        flow_data = []
        for app in app_names:
            app_data = filtered_data[filtered_data['app_name'] == app]
            if len(app_data) == 0:
                continue
            
            # Get sessions and their page sequences
            sessions_with_pages = app_data[app_data['page_name'] != ''].groupby('session_id')['page_name'].apply(list).reset_index()
            
            if len(sessions_with_pages) == 0:
                continue
                
            # Find common entry and exit points
            entry_pages = {}
            exit_pages = {}
            single_page_sessions = 0
            
            for _, row in sessions_with_pages.iterrows():
                pages = row['page_name']
                if len(pages) > 0:
                    entry_page = pages[0]
                    exit_page = pages[-1]
                    
                    entry_pages[entry_page] = entry_pages.get(entry_page, 0) + 1
                    exit_pages[exit_page] = exit_pages.get(exit_page, 0) + 1
                    
                    if len(pages) == 1:
                        single_page_sessions += 1
            
            # Get top entry and exit points
            if entry_pages:
                top_entry = max(entry_pages, key=entry_pages.get)
                top_exit = max(exit_pages, key=exit_pages.get)
                drop_off_rate = (single_page_sessions / len(sessions_with_pages)) * 100
                
                flow_data.append({
                    'app': app,
                    'top_entry_page': top_entry,
                    'entry_sessions': entry_pages[top_entry],
                    'top_exit_page': top_exit,
                    'exit_sessions': exit_pages[top_exit],
                    'single_page_dropout_rate': drop_off_rate
                })
        
        if not flow_data:
            fig = go.Figure()
            fig.add_annotation(text="No user journey data available", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='User Flow Analysis')
            return fig
        
        # Create visualization for drop-off rates
        flow_df = pd.DataFrame(flow_data)
        
        fig = px.bar(flow_df, x='app', y='single_page_dropout_rate',
                     title='User Drop-off Rate by App (Single Page Sessions)',
                     labels={'single_page_dropout_rate': 'Drop-off Rate (%)', 'app': 'Application'},
                     hover_data={'top_entry_page': True, 'top_exit_page': True})
        
        return fig
    
    # App Performance Issues 
    @callback(
        Output('completion-rate', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_completion_rate(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Identify potential usability issues
        issues_data = []
        for app in app_names:
            app_data = filtered_data[filtered_data['app_name'] == app]
            if len(app_data) == 0:
                continue
                
            total_sessions = len(app_data)
            
            # Define potential issues
            quick_exits = len(app_data[app_data['duration'] < 10]) / total_sessions * 100  # <10s sessions
            no_connection = len(app_data[app_data['connection'] == False]) / total_sessions * 100 if 'connection' in app_data.columns else 0
            single_screen = len(app_data[app_data['widget_name'] == '']) / total_sessions * 100  # No widget interaction
            
            issues_data.extend([
                {'app': app, 'issue_type': 'Quick Exits (<10s)', 'percentage': quick_exits},
                {'app': app, 'issue_type': 'Connection Issues', 'percentage': no_connection},
                {'app': app, 'issue_type': 'No Interaction', 'percentage': single_screen}
            ])
        
        if not issues_data:
            fig = go.Figure()
            fig.add_annotation(text="No performance issue data available", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='App Performance Issues')
            return fig
        
        issues_df = pd.DataFrame(issues_data)
        
        fig = px.bar(issues_df, x='app', y='percentage', color='issue_type',
                     title='Potential Usability Issues by App',
                     labels={'percentage': 'Percentage of Sessions', 'app': 'Application'},
                     color_discrete_map={'Quick Exits (<10s)': 'red', 'Connection Issues': 'orange', 'No Interaction': 'yellow'})
        
        return fig
    
    # Device Performance
    @callback(
        Output('device-performance', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_device_performance(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Get device performance metrics
        device_performance = filtered_data.groupby(['device_type', 'os']).agg({
            'duration': 'mean',
            'distinct_id': 'nunique'
        }).reset_index()
        
        fig = px.scatter(device_performance, x='duration', y='distinct_id', 
                        color='device_type', size='distinct_id',
                        title='Device Performance: Avg Duration vs User Count',
                        labels={'duration': 'Average Session Duration (s)', 'distinct_id': 'Number of Users'})
        
        return fig
    
    # Network Quality
    @callback(
        Output('network-quality', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_network_quality(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Connection status
        connection_data = filtered_data['connection'].value_counts()
        
        fig = px.pie(values=connection_data.values, names=connection_data.index,
                     title='Connection Status Distribution')
        
        return fig
    
    # Version Performance
    @callback(
        Output('version-performance', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_version_performance(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Extract app version from properties
        filtered_data['app_version'] = filtered_data['props'].apply(
            lambda x: x.get('$app_version', 'Unknown') if isinstance(x, dict) else 'Unknown'
        )
        
        version_metrics = filtered_data.groupby(['app_name', 'app_version']).agg({
            'distinct_id': 'nunique',
            'duration': 'mean'
        }).reset_index()
        
        fig = px.bar(version_metrics, x='app_version', y='distinct_id', color='app_name',
                     title='User Distribution by App Version',
                     labels={'distinct_id': 'Number of Users', 'app_version': 'App Version'})
        
        return fig
    
    # Geographic Performance
    @callback(
        Output('geographic-performance', 'figure'),
        [Input('app-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('device-filter', 'value')]
    )
    def update_geographic_performance(app_names, start_date, end_date, device_type):
        if not app_names:
            return go.Figure()
        
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        
        # Performance by country
        geo_performance = filtered_data.groupby('country').agg({
            'duration': ['mean', 'count'],
            'distinct_id': 'nunique'
        }).reset_index()
        
        geo_performance.columns = ['country', 'avg_duration', 'session_count', 'user_count']
        geo_performance = geo_performance[geo_performance['session_count'] >= 5]  # Filter countries with few sessions
        
        fig = px.scatter(geo_performance, x='avg_duration', y='user_count', 
                        size='session_count', hover_name='country',
                        title='Geographic Performance: Duration vs Users by Country',
                        labels={'avg_duration': 'Average Session Duration (s)', 'user_count': 'Number of Users'})
        
        return fig