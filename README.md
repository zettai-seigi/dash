# PostHog Analytics Dashboard - Streamlit Edition

A comprehensive analytics dashboard built with Streamlit for analyzing PostHog event data across 5 applications: BPS, Lineup, bspace, btech, and etam.

## Features

### 📊 Executive Overview
- **KPI Metrics**: Real-time cards showing Total Users, Sessions, Average Duration, Bounce Rate
- **Daily Active Users**: Time series trend visualization
- **App Comparison**: Side-by-side usage metrics across all applications
- **Geographic Distribution**: Interactive world map showing user distribution

### 📱 Usage Analytics
- **Session Duration**: Distribution histogram with statistical insights
- **Feature Usage**: Top widgets and features by interaction count
- **Platform Breakdown**: Device type and OS distribution charts
- **Network Analysis**: WiFi vs Cellular usage patterns
- **Activity Heatmap**: Hour-by-day usage intensity visualization

### 🎯 Usability Insights
- **Engagement Scatter**: Session duration vs event count analysis
- **Screen Flow**: Treemap visualization of screen popularity
- **User Journeys**: Page navigation patterns and paths
- **Session Quality**: Completion rates and quality metrics

### ⚡ Technical Performance
- **Device Metrics**: Performance breakdown by device category
- **Connection Quality**: Network stability and drop rates
- **Version Adoption**: User distribution across app versions
- **Geographic Performance**: Country-wise performance metrics
- **Raw Data Explorer**: Filterable data table with export options

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Streamlit and dependencies:
```bash
pip install streamlit plotly pandas numpy
```

3. Ensure your CSV data files are in the project directory:
- `data_app_posthog_BPS.csv`
- `data_app_posthog_Lineup.csv`
- `data_app_posthog_bspace.csv`
- `data_app_posthog_btech.csv`
- `data_app_posthog_etam.csv`

## Usage

1. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. The dashboard will automatically open in your browser at `http://localhost:8501`

3. Use the sidebar filters to customize your analysis:
   - **Apps**: Multi-select specific applications
   - **Date Range**: Choose analysis time period
   - **Device Type**: Filter by Mobile/Desktop
   - **Country**: Geographic filtering

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

## Project Structure

```
dash/
├── streamlit_app.py          # Main Streamlit application
├── data_app_posthog_*.csv    # PostHog event data files (5 apps)
├── requirements.txt          # Python dependencies
└── CLAUDE.md                 # Development documentation
```

## Customization

### Adding New Metrics
1. Modify the `process_data()` function in `streamlit_app.py` to extract new parameters from the JSON properties
2. Add new visualization functions using Plotly Express or Graph Objects
3. Update the tab structure to include new chart sections

### Customizing Visualizations
- All charts use Plotly for interactive visualizations
- Modify color schemes by updating the `px` color parameters
- Add custom CSS in the `st.markdown()` section at the top of the file
- Adjust layout using Streamlit's column and container components

## Data Sources

This dashboard processes PostHog event data with the following structure:
- `uuid`: Event ID
- `event`: Event type (Capture, $autocapture, $pageleave)
- `properties`: JSON string with event metadata
- `distinct_id`: User identifier
- `timestamp`: Event timestamp
- `app_name`: Application name (added during processing)

## Performance Optimization

### Caching
- Streamlit's `@st.cache_data` decorator is used for data loading
- Cached data persists across user sessions to improve performance
- Clear cache using the "C" menu in the top-right corner

### Best Practices
- For large datasets (>100K rows), consider implementing pagination
- Use data sampling for initial exploration: `df.sample(n=10000)`
- Enable Streamlit's production settings for deployment:
  ```toml
  # .streamlit/config.toml
  [server]
  maxUploadSize = 200
  enableCORS = false
  enableXsrfProtection = true
  ```

### Deployment Options
- **Streamlit Cloud**: Free hosting at share.streamlit.io
- **Docker**: Container deployment for scalability
- **Heroku/AWS/GCP**: Cloud platform deployment
- **Corporate Network**: Internal deployment with authentication

## Troubleshooting

### Common Issues

1. **File Not Found Error**
   - Ensure all CSV files are in the same directory as `streamlit_app.py`
   - Check file naming: `data_app_posthog_{app_name}.csv`

2. **Memory Issues**
   - Reduce data sample size in `load_data()` function
   - Implement incremental data loading
   - Use data aggregation for large datasets

3. **Slow Performance**
   - Enable caching with `@st.cache_data`
   - Pre-aggregate data for complex visualizations
   - Consider using a database instead of CSV files

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with sample data
5. Submit a pull request

## License

This project is open source and available under the MIT License.