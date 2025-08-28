# PostHog Analytics Dashboard

A comprehensive usage and usability dashboard for analyzing PostHog data across 5 applications: BPS, Lineup, bspace, btech, and etam.

## Features

### 📊 Executive Overview
- **KPI Cards**: Total Users, Sessions, Average Duration, Bounce Rate
- **Time Series**: Daily Active Users trend
- **App Comparison**: Usage metrics across all apps
- **Geographic Distribution**: User distribution by country

### 📱 Usage Analytics
- **Session Duration Distribution**: Histogram of session lengths
- **Feature Usage**: Most used widgets/features
- **Platform Breakdown**: OS and device type distribution
- **Network Analysis**: WiFi vs Cellular usage
- **Hourly Usage Pattern**: Usage heatmap by hour and day

### 🎯 Usability Insights
- **Engagement Analysis**: Session duration vs events scatter plot
- **Screen Popularity**: Treemap of most visited screens
- **User Journey**: Most visited pages/screens
- **Completion Rate**: Session completion metrics

### ⚡ Technical Performance
- **Device Performance**: Performance metrics by device type
- **Network Quality**: Connection status distribution
- **Version Analysis**: User distribution by app version
- **Geographic Performance**: Performance metrics by country
- **Data Table**: Raw data sample with filtering

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Ensure your CSV files are in the same directory:
- `data_app_posthog_BPS.csv`
- `data_app_posthog_Lineup.csv`
- `data_app_posthog_bspace.csv`
- `data_app_posthog_btech.csv`
- `data_app_posthog_etam.csv`

## Usage

1. Run the dashboard:
```bash
python app.py
```

2. Open your browser to `http://localhost:8050`

3. Use the filters to analyze specific:
   - Apps (multi-select)
   - Date ranges
   - Device types

## Data Dictionary

### Core Metrics
- **Users**: Unique count of `distinct_id`
- **Sessions**: Unique count of `session_id`
- **Duration**: Session length in seconds
- **Bounce Rate**: Sessions under 30 seconds / Total sessions
- **Completion Rate**: Sessions over 60 seconds / Total sessions

### Key Parameters
- `distinct_id`: User identifier (email)
- `session_id`: Session identifier
- `Duration`: Session duration from properties
- `Page_Name`: Current page/screen
- `Widget_Name`: UI component name
- `$device_type`: Mobile/Desktop
- `$os`: Operating system
- `$geoip_country_name`: User location
- `Connection`: Network connection status
- `$network_wifi`: WiFi usage indicator

## Architecture

- **app.py**: Main dashboard application
- **callbacks.py**: Additional callback functions for charts
- **requirements.txt**: Python dependencies

## Customization

### Adding New Metrics
1. Modify the `process_data()` function to extract new parameters
2. Add new callback functions in `callbacks.py`
3. Update the layout in `app.py` to include new charts

### Styling
- Uses Bootstrap 5 for responsive layout
- Plotly themes can be customized in chart creation
- Add custom CSS by modifying the `external_stylesheets`

## Data Sources

This dashboard processes PostHog event data with the following structure:
- `uuid`: Event ID
- `event`: Event type (Capture, $autocapture, $pageleave)
- `properties`: JSON string with event metadata
- `distinct_id`: User identifier
- `timestamp`: Event timestamp
- `app_name`: Application name (added during processing)

## Performance Notes

- Large datasets may require pagination or sampling
- Consider using Dash caching for production deployments
- Database integration recommended for real-time data