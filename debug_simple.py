import dash
from dash import dcc, html, Input, Output, callback

# Simple test app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Simple Test"),
    html.Div(id="test-output"),
    dcc.Dropdown(
        id="test-dropdown",
        options=[{"label": "Option 1", "value": "1"}, {"label": "Option 2", "value": "2"}],
        value="1"
    )
])

@callback(
    Output("test-output", "children"),
    Input("test-dropdown", "value")
)
def update_output(value):
    return f"Selected: {value}"

if __name__ == "__main__":
    app.run(debug=True, port=8051)