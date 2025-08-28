import dash
from dash import dcc, html, Input, Output, callback, dash_table
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

# Import additional callbacks
from callbacks import register_additional_callbacks

# Load and process data
def load_data():
    """Load sample data for testing"""
    print("Loading sample data for faster testing...")
    
    apps = ['BPS', 'Lineup', 'bspace', 'btech', 'etam']
    all_data = []
    
    for app in apps:
        # Create sample data
        sample_data = {
            'uuid': [f'sample-{app}-{i}' for i in range(500)],
            'event': ['Capture'] * 500,
            'properties': [f'{{"Widget_Name": "Button_{i%20}", "Page_Name": "Page_{i%10}", "Duration": {np.random.randint(10, 300)}, "$device_type": "{"Mobile" if i%2 else "Desktop"}", "$session_id": "session_{i//10}", "$geoip_country_name": "{"US" if i%3==0 else "UK" if i%3==1 else "Canada"}"}}' for i in range(500)],
            'distinct_id': [f'user{i%100}@{app.lower()}.com' for i in range(500)],
            'timestamp': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(500)],
            'app_name': [app] * 500
        }
        df = pd.DataFrame(sample_data)
        all_data.append(df)
        print(f"Created sample data for {app}: {len(df)} rows")
    
    return pd.concat(all_data, ignore_index=True)

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
                import re
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
    
    # Create date column
    df['date'] = df['timestamp'].dt.date
    
    return df

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
])
app.title = "📊 Analytics Dashboard - Usage & Usability Insights"

# Load and process data
print("Starting data load...")
raw_data = load_data()
print(f"Raw data loaded: {len(raw_data)} rows")
print("Processing data...")
data = process_data(raw_data)
print(f"Data processed: {len(data)} rows")

# Custom CSS
custom_style = {
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    'backgroundColor': '#f8fafc',
    'minHeight': '100vh'
}

# Custom CSS injection
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-radius: 0 0 20px 20px;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 1rem;
            padding: 1.5rem;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 25px rgba(0,0,0,0.12);
        }
        .chart-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            margin-bottom: 2rem;
            padding: 0;
            overflow: hidden;
        }
        .control-panel {
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        .tab-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            overflow: hidden;
        }
        .dash-tab {
            background: #f1f5f9 !important;
            border: none !important;
            border-radius: 10px 10px 0 0 !important;
            color: #64748b !important;
            font-weight: 500 !important;
            margin-right: 2px !important;
            transition: all 0.2s ease !important;
        }
        .dash-tab:hover {
            background: #e2e8f0 !important;
            color: #475569 !important;
        }
        .dash-tab--selected {
            background: white !important;
            color: #1e293b !important;
            font-weight: 600 !important;
            border-bottom: 3px solid #667eea !important;
        }
        .metric-number {
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        body {
            background-color: #f8fafc !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Dashboard layout
app.layout = html.Div([
    
    # Header
    html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-line me-3", style={'fontSize': '2rem'}),
                html.Div([
                    html.H1("Analytics Dashboard", className="mb-1", style={'fontSize': '2.5rem', 'fontWeight': '700'}),
                    html.P("Usage & Usability Insights for 5 Applications", className="mb-0 opacity-75", style={'fontSize': '1.1rem', 'fontWeight': '400'})
                ], className="d-inline-block")
            ], className="d-flex align-items-center")
        ], className="container")
    ], className="main-header py-4 text-white"),
    
    # Controls Panel
    html.Div([
        html.Div([
            html.H5("📊 Filter Controls", className="mb-3", style={'color': '#1e293b', 'fontWeight': '600'}),
            html.Div([
                html.Div([
                    html.Label("🏢 Applications", className="form-label fw-semibold text-muted mb-2"),
                    dcc.Dropdown(
                        id='app-filter',
                        options=[{'label': f"📱 {app}", 'value': app} for app in data['app_name'].unique()],
                        value=data['app_name'].unique().tolist(),
                        multi=True,
                        style={'borderRadius': '10px'},
                        className="mb-3",
                        placeholder="Select applications..."
                    )
                ], className="col-md-4"),
                
                html.Div([
                    html.Label("📅 Date Range", className="form-label fw-semibold text-muted mb-2"),
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=data['date'].min(),
                        end_date=data['date'].max(),
                        display_format='YYYY-MM-DD',
                        style={'borderRadius': '10px'},
                        className="mb-3"
                    )
                ], className="col-md-4"),
                
                html.Div([
                    html.Label("📱 Device Type", className="form-label fw-semibold text-muted mb-2"),
                    dcc.Dropdown(
                        id='device-filter',
                        options=[{'label': '🌐 All Devices', 'value': 'all'}] + 
                                [{'label': f"📱 {dt}", 'value': dt} for dt in data['device_type'].unique()],
                        value='all',
                        style={'borderRadius': '10px'},
                        className="mb-3"
                    )
                ], className="col-md-4"),
            ], className="row")
        ], className="container")
    ], className="control-panel mx-auto", style={'maxWidth': '1200px'}),

    # KPI Cards
    html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-users text-primary", style={'fontSize': '2.5rem', 'marginBottom': '1rem'}),
                html.Div(id="total-users", className="metric-number", children="Loading..."),
                html.Div("Total Users", className="metric-label")
            ], className="metric-card text-center")
        ], className="col-lg-3 col-md-6"),
        
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-line text-success", style={'fontSize': '2.5rem', 'marginBottom': '1rem'}),
                html.Div(id="total-sessions", className="metric-number", children="Loading..."),
                html.Div("Total Sessions", className="metric-label")
            ], className="metric-card text-center")
        ], className="col-lg-3 col-md-6"),
        
        html.Div([
            html.Div([
                html.I(className="fas fa-clock text-info", style={'fontSize': '2.5rem', 'marginBottom': '1rem'}),
                html.Div(id="avg-duration", className="metric-number", children="Loading..."),
                html.Div("Average Duration", className="metric-label")
            ], className="metric-card text-center")
        ], className="col-lg-3 col-md-6"),
        
        html.Div([
            html.Div([
                html.I(className="fas fa-bounce text-warning", style={'fontSize': '2.5rem', 'marginBottom': '1rem'}),
                html.Div(id="bounce-rate", className="metric-number", children="Loading..."),
                html.Div("Bounce Rate", className="metric-label")
            ], className="metric-card text-center")
        ], className="col-lg-3 col-md-6"),
    ], className="row container-fluid", style={'maxWidth': '1200px', 'margin': '0 auto'}),
    
    # Tabs for different views
    html.Div([
        dcc.Tabs(id="main-tabs", value="overview", className="tab-container mx-auto", style={'maxWidth': '1200px'}, children=[
        
        # Tab 1: Executive Overview
        dcc.Tab(label="📊 Executive Overview", value="overview", children=[
            html.Div([
                # Charts
                html.Div([
                    html.Div([
                        dcc.Graph(id="daily-active-users")
                    ], className="col-md-6"),
                    
                    html.Div([
                        dcc.Graph(id="app-comparison")
                    ], className="col-md-6"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id="geographic-distribution", config={'displayModeBar': False})
                    ], className="chart-container")
                ], className="col-md-12"),
            ], className="row container-fluid", style={'maxWidth': '1200px', 'margin': '0 auto'}),
        ], style={'padding': '2rem'})
        ]),
        
        # Tab 2: Usage Analytics
        dcc.Tab(label="📱 Usage Analytics", value="usage", children=[
            html.Div([
                html.Div([
                    html.Div([
                        dcc.Graph(id="session-duration-dist")
                    ], className="col-md-6"),
                    
                    html.Div([
                        dcc.Graph(id="feature-usage")
                    ], className="col-md-6"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id="platform-breakdown")
                    ], className="col-md-6"),
                    
                    html.Div([
                        dcc.Graph(id="network-analysis")
                    ], className="col-md-6"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id="hourly-usage")
                    ], className="col-md-12"),
                ], className="row"),
            ])
        ]),
        
        # Tab 3: Usability Insights
        dcc.Tab(label="🎯 Usability Insights", value="usability", children=[
            html.Div([
                html.Div([
                    html.Div([
                        dcc.Graph(id="engagement-scatter")
                    ], className="col-md-6"),
                    
                    html.Div([
                        dcc.Graph(id="screen-popularity")
                    ], className="col-md-6"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id="user-journey")
                    ], className="col-md-12"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id="completion-rate")
                    ], className="col-md-12"),
                ], className="row"),
            ])
        ]),
        
        # Tab 4: Technical Performance
        dcc.Tab(label="⚡ Technical Performance", value="performance", children=[
            html.Div([
                html.Div([
                    html.Div([
                        dcc.Graph(id="device-performance")
                    ], className="col-md-6"),
                    
                    html.Div([
                        dcc.Graph(id="network-quality")
                    ], className="col-md-6"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        dcc.Graph(id="version-performance")
                    ], className="col-md-6"),
                    
                    html.Div([
                        dcc.Graph(id="geographic-performance")
                    ], className="col-md-6"),
                ], className="row"),
                
                html.Div([
                    html.Div([
                        html.H4("Data Sample"),
                        dash_table.DataTable(
                            id='data-table',
                            columns=[
                                {"name": "App", "id": "app_name"},
                                {"name": "Event", "id": "event"},
                                {"name": "User", "id": "distinct_id"},
                                {"name": "Duration", "id": "duration"},
                                {"name": "Page", "id": "page_name"},
                                {"name": "Device", "id": "device_type"},
                                {"name": "OS", "id": "os"},
                                {"name": "Country", "id": "country"},
                            ],
                            page_size=10,
                            sort_action="native",
                            filter_action="native"
                        )
                    ], className="col-md-12"),
                ], className="row py-4"),
            ])
        ])
    ])
], style=custom_style)

# Callback for filtering data
def filter_data(app_names, date_range, device_type):
    """Filter data based on user selections"""
    filtered_data = data[data['app_name'].isin(app_names)]
    
    if date_range:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data['date'] >= pd.to_datetime(start_date).date()) &
            (filtered_data['date'] <= pd.to_datetime(end_date).date())
        ]
    
    if device_type != 'all':
        filtered_data = filtered_data[filtered_data['device_type'] == device_type]
    
    return filtered_data

# Callbacks for KPI cards
@callback(
    [Output('total-users', 'children'),
     Output('total-sessions', 'children'),
     Output('avg-duration', 'children'),
     Output('bounce-rate', 'children')],
    [Input('app-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_kpis(app_names, start_date, end_date, device_type):
    print(f"DEBUG: update_kpis called with apps={app_names}, device={device_type}")
    
    if not app_names:
        print("DEBUG: No apps selected, returning zeros")
        return "0", "0", "0s", "0%"
    
    try:
        filtered_data = filter_data(app_names, [start_date, end_date], device_type)
        print(f"DEBUG: Filtered data has {len(filtered_data)} rows")
        
        total_users = filtered_data['distinct_id'].nunique()
        
        # Count sessions - handle empty/null session_ids properly
        valid_sessions = filtered_data[filtered_data['session_id'] != '']['session_id']
        total_sessions = valid_sessions.nunique() if len(valid_sessions) > 0 else filtered_data.groupby('distinct_id').size().sum()
        
        # Calculate average duration of valid durations (> 0)
        valid_durations = filtered_data[filtered_data['duration'] > 0]['duration']
        avg_duration = f"{valid_durations.mean():.1f}s" if len(valid_durations) > 0 else "0s"
        
        # Calculate bounce rate (sessions < 30 seconds) - use unique sessions, not events
        if len(valid_sessions) > 0:
            session_durations = filtered_data.groupby('session_id')['duration'].max()
            short_sessions = len(session_durations[session_durations < 30])
            bounce_rate = f"{(short_sessions / len(session_durations) * 100):.1f}%"
        else:
            short_sessions = len(filtered_data[filtered_data['duration'] < 30])
            bounce_rate = f"{(short_sessions / len(filtered_data) * 100):.1f}%" if len(filtered_data) > 0 else "0%"
        
        result = (f"{total_users:,}", f"{total_sessions:,}", avg_duration, bounce_rate)
        print(f"DEBUG: Returning KPIs: {result}")
        return result
        
    except Exception as e:
        print(f"DEBUG: Error in update_kpis: {e}")
        return "Error", "Error", "Error", "Error"

# Callbacks for charts
@callback(
    Output('daily-active-users', 'figure'),
    [Input('app-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_daily_active_users(app_names, start_date, end_date, device_type):
    if not app_names:
        return go.Figure()
    
    filtered_data = filter_data(app_names, [start_date, end_date], device_type)
    
    daily_users = filtered_data.groupby(['date', 'app_name'])['distinct_id'].nunique().reset_index()
    
    fig = px.line(daily_users, x='date', y='distinct_id', color='app_name',
                  title='Daily Active Users by App',
                  labels={'distinct_id': 'Daily Active Users', 'date': 'Date'})
    
    return fig

@callback(
    Output('app-comparison', 'figure'),
    [Input('app-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_app_comparison(app_names, start_date, end_date, device_type):
    if not app_names:
        return go.Figure()
    
    filtered_data = filter_data(app_names, [start_date, end_date], device_type)
    
    app_metrics = filtered_data.groupby('app_name').agg({
        'distinct_id': 'nunique',
        'duration': 'mean',
        'event': 'count'
    }).reset_index()
    
    app_metrics.columns = ['App', 'Users', 'Avg Duration', 'Events']
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=app_metrics['App'], y=app_metrics['Users'], name='Users'),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=app_metrics['App'], y=app_metrics['Avg Duration'], 
                   mode='lines+markers', name='Avg Duration (s)'),
        secondary_y=True,
    )
    
    fig.update_xaxes(title_text="Application")
    fig.update_yaxes(title_text="Number of Users", secondary_y=False)
    fig.update_yaxes(title_text="Average Duration (seconds)", secondary_y=True)
    
    fig.update_layout(title_text="App Comparison: Users vs Average Duration")
    
    return fig

@callback(
    Output('geographic-distribution', 'figure'),
    [Input('app-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_geographic_distribution(app_names, start_date, end_date, device_type):
    if not app_names:
        return go.Figure()
    
    filtered_data = filter_data(app_names, [start_date, end_date], device_type)
    
    geo_data = filtered_data.groupby('country')['distinct_id'].nunique().reset_index()
    geo_data = geo_data.sort_values('distinct_id', ascending=False).head(10)
    
    fig = px.bar(geo_data, x='distinct_id', y='country', orientation='h',
                 title='Top 10 Countries by User Count',
                 labels={'distinct_id': 'Number of Users', 'country': 'Country'})
    
    return fig

# Additional callbacks for other charts...
@callback(
    Output('data-table', 'data'),
    [Input('app-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_data_table(app_names, start_date, end_date, device_type):
    if not app_names:
        return []
    
    filtered_data = filter_data(app_names, [start_date, end_date], device_type)
    
    return filtered_data[['app_name', 'event', 'distinct_id', 'duration', 
                         'page_name', 'device_type', 'os', 'country']].head(50).to_dict('records')

# Register additional callbacks
register_additional_callbacks(app, data, filter_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)