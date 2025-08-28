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
            except Exception as e1:
                print(f"Standard read failed for {app}: {e1}")
                
                # Strategy 2: Read with error handling and encoding fixes
                try:
                    df = pd.read_csv(f'data_app_posthog_{app}.csv', 
                                   on_bad_lines='skip', 
                                   encoding='utf-8', 
                                   quoting=3,  # QUOTE_NONE
                                   engine='python')
                except Exception as e2:
                    print(f"Python engine read failed for {app}: {e2}")
                    
                    # Strategy 3: Read only first N rows to avoid corrupted data at end
                    try:
                        df = pd.read_csv(f'data_app_posthog_{app}.csv', 
                                       on_bad_lines='skip',
                                       nrows=200000,  # Limit rows to avoid corruption
                                       encoding='utf-8')
                    except Exception as e3:
                        print(f"Limited row read failed for {app}: {e3}")
            
            if df is not None:
                # Select only the columns we need
                required_cols = ['uuid', 'event', 'properties', 'distinct_id', 'timestamp']
                available_cols = [col for col in required_cols if col in df.columns]
                df = df[available_cols].copy()
                
                df['app_name'] = app
                all_data.append(df)
                print(f"Successfully loaded {app}: {len(df)} rows")
            else:
                print(f"Failed to load {app} - creating sample data")
                raise Exception("All read strategies failed")
        except Exception as e:
            print(f"Error loading {app}: {e}")
            # Create sample data if file doesn't exist
            sample_data = {
                'uuid': [f'sample-{i}' for i in range(100)],
                'event': ['Capture'] * 100,
                'properties': ['{}'] * 100,
                'distinct_id': [f'user{i}@example.com' for i in range(100)],
                'timestamp': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(100)],
                'app_name': [app] * 100
            }
            df = pd.DataFrame(sample_data)
            all_data.append(df)
    
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
app = dash.Dash(__name__, external_stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'])
app.title = "PostHog Analytics Dashboard - 5 Apps Usage & Usability"

# Load and process data
raw_data = load_data()
data = process_data(raw_data)

# Dashboard layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("PostHog Analytics Dashboard", className="text-center mb-4"),
        html.H2("Usage & Usability Analysis for 5 Applications", className="text-center mb-4 text-muted"),
    ], className="container-fluid py-3 bg-primary text-white"),
    
    # Controls
    html.Div([
        html.Div([
            html.Label("Select Apps:"),
            dcc.Dropdown(
                id='app-filter',
                options=[{'label': app, 'value': app} for app in data['app_name'].unique()],
                value=data['app_name'].unique().tolist(),
                multi=True
            )
        ], className="col-md-4"),
        
        html.Div([
            html.Label("Date Range:"),
            dcc.DatePickerRange(
                id='date-range',
                start_date=data['date'].min(),
                end_date=data['date'].max(),
                display_format='YYYY-MM-DD'
            )
        ], className="col-md-4"),
        
        html.Div([
            html.Label("Device Type:"),
            dcc.Dropdown(
                id='device-filter',
                options=[{'label': 'All', 'value': 'all'}] + 
                        [{'label': dt, 'value': dt} for dt in data['device_type'].unique()],
                value='all'
            )
        ], className="col-md-4"),
    ], className="row container-fluid py-3"),
    
    # Tabs
    dcc.Tabs(id="tabs", value="overview", children=[
        
        # Tab 1: Executive Overview
        dcc.Tab(label="📊 Executive Overview", value="overview", children=[
            html.Div([
                # KPI Cards
                html.Div([
                    html.Div([
                        html.H3(id="total-users", children="0"),
                        html.P("Total Users")
                    ], className="col-md-3 text-center bg-light p-3 m-2 rounded"),
                    
                    html.Div([
                        html.H3(id="total-sessions", children="0"),
                        html.P("Total Sessions")
                    ], className="col-md-3 text-center bg-light p-3 m-2 rounded"),
                    
                    html.Div([
                        html.H3(id="avg-duration", children="0s"),
                        html.P("Avg Session Duration")
                    ], className="col-md-3 text-center bg-light p-3 m-2 rounded"),
                    
                    html.Div([
                        html.H3(id="bounce-rate", children="0%"),
                        html.P("Bounce Rate")
                    ], className="col-md-3 text-center bg-light p-3 m-2 rounded"),
                ], className="row container-fluid py-3"),
                
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
                        dcc.Graph(id="geographic-distribution")
                    ], className="col-md-12"),
                ], className="row"),
            ])
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
        ]),
    ]),
], className="container-fluid")

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
    if not app_names:
        return "0", "0", "0s", "0%"
    
    filtered_data = filter_data(app_names, [start_date, end_date], device_type)
    
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
    
    return f"{total_users:,}", f"{total_sessions:,}", avg_duration, bounce_rate

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