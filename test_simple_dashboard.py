#!/usr/bin/env python3

import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd

# Create simple test data
data = pd.DataFrame({
    'app_name': ['BPS', 'Lineup', 'BPS', 'Lineup'] * 25,
    'distinct_id': [f'user_{i}@test.com' for i in range(100)],
    'duration': [30, 45, 120, 60] * 25,
    'date': pd.date_range('2024-01-01', periods=100)
})

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Test Dashboard"),
    
    dcc.Dropdown(
        id='app-filter',
        options=[{'label': app, 'value': app} for app in data['app_name'].unique()],
        value=data['app_name'].unique().tolist(),
        multi=True
    ),
    
    html.Div([
        html.Div(id="total-users", children="Loading..."),
        html.Div(id="total-sessions", children="Loading..."),
    ]),
    
    dcc.Graph(id="test-chart")
])

@callback(
    [Output('total-users', 'children'),
     Output('total-sessions', 'children')],
    [Input('app-filter', 'value')]
)
def update_metrics(app_names):
    if not app_names:
        return "0", "0"
    
    filtered = data[data['app_name'].isin(app_names)]
    users = filtered['distinct_id'].nunique()
    sessions = len(filtered)
    
    return f"Users: {users}", f"Sessions: {sessions}"

@callback(
    Output('test-chart', 'figure'),
    [Input('app-filter', 'value')]
)
def update_chart(app_names):
    if not app_names:
        return px.bar()
    
    filtered = data[data['app_name'].isin(app_names)]
    fig = px.bar(filtered.groupby('app_name')['distinct_id'].nunique().reset_index(), 
                 x='app_name', y='distinct_id', title='Users by App')
    return fig

if __name__ == '__main__':
    print("Starting simple test dashboard...")
    app.run(debug=True, port=8051)