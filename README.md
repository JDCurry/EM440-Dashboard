# Washington Climate-Fire Risk Intelligence Dashboard

A Streamlit-based interactive dashboard for Washington State emergency management decision support.

## Purpose
This dashboard helps state and county emergency managers identify and prioritize counties facing elevated wildfire risk due to changing climate patterns by integrating 2019-2024 climate data with historical fire patterns and community exposure.

## Features
- **Interactive Choropleth Map**: County-level risk visualization
- **Real-Time Filtering**: Filter by risk category, climate trend, and population
- **Risk Metrics**: Composite scoring based on heat, drought, fire history, and WUI exposure
- **Data Export**: Download filtered datasets for further analysis

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Create project directory:**
```bash
mkdir wa_climate_fire_dashboard
cd wa_climate_fire_dashboard
```

2. **Set up data folder:**
```bash
mkdir data
# Copy these files to data/:
# - WA_Climate_Fire_Dashboard_Data.csv
# - wa_counties.geojson
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the dashboard:**
```bash
streamlit run streamlit_dashboard.py
```

5. **View in browser:**
The dashboard will automatically open at `http://localhost:8501`

## Project Structure
```
wa_climate_fire_dashboard/
├── streamlit_dashboard.py   # Main application
├── requirements.txt                  # Python dependencies
├── data/
│   ├── WA_Climate_Fire_Dashboard_Data.csv
│   └── wa_counties.geojson
└── README.md                         # This file
```

## Data Sources
- **Climate Data**: NOAA Climate Normals, 2019-2024
- **Wildfire Events**: NOAA Storm Events Database
- **WUI Data**: USDA Forest Service Wildland-Urban Interface
- **Demographics**: U.S. Census Bureau, 2020

## Risk Score Methodology

The Climate-Fire Risk Score (0-100) is calculated as:

```
Risk Score = Heat Stress + Drought Stress + Fire History + WUI Exposure

Where:
- Heat Stress (0-30): Based on temperature anomalies (Z-scores)
- Drought Stress (0-30): Based on precipitation deficits (Z-scores)
- Fire History (0-30): Log-normalized historical fire count
- WUI Exposure (0-25): Weighted combination of interface/intermix percentages
```

**Risk Categories:**
- **Critical**: 70-100 (immediate action required)
- **High**: 55-69 (priority for mitigation investments)
- **Moderate**: 40-54 (monitor and plan)
- **Low**: 0-39 (baseline monitoring)

## Usage Scenarios

### For State Mitigation Planners
1. Filter to "High" risk counties
2. Review climate trends and population at risk
3. Export data for grant applications

### For County Emergency Managers
1. Select your county on the map
2. Review detailed pop-up with local metrics
3. Compare your county to state averages

### For Regional Coordinators
1. Filter by climate trend "Warming & Drying"
2. Identify multi-county patterns
3. Plan regional resource pre-positioning

## Customization

### Modify Risk Score Weights
Edit lines 115-120 in `streamlit_dashboard.py`:
```python
dashboard_data['climate_fire_risk_score'] = (
    dashboard_data['heat_stress'] * 25 +     # Adjust weight
    dashboard_data['drought_stress'] * 20 +  # Adjust weight
    dashboard_data['fire_history_norm'] * 30 +  # Adjust weight
    dashboard_data['wui_exposure'] * 25      # Adjust weight
)
```

### Change Map Style
Edit line 184 in `streamlit_dashboard.py`:
```python
tiles='OpenStreetMap'  # Options: 'CartoDB positron', 'Stamen Terrain'
```

### Add New Filters
Add to sidebar section (lines 90-110) following the existing pattern.


## Troubleshooting

**Map not loading?**
- Check that `wa_counties.geojson` has property `GEOID` matching `county_fips`
- Verify GeoJSON is valid using [geojson.io](http://geojson.io)

**Data not matching?**
- Ensure county names are uppercase in CSV
- Check for missing values in key columns

**Slow performance?**
- Reduce map complexity (simplify GeoJSON)
- Enable Streamlit caching (already implemented)

## Future Enhancements
- [ ] Time series animation showing climate trends
- [ ] ML-based fire risk forecasting
- [ ] Integration with real-time weather APIs
- [ ] Mobile-responsive design improvements
- [ ] Export to PDF report functionality

## License
Educational use - Pierce College EM440: GIS Emergency Management Course Assignment

## Author
[Josh Curry]  
[EM440: Geographic Information Systems (GIS) for EM]  
November 2025

## Acknowledgments
- NOAA National Centers for Environmental Information
- USDA Forest Service
- Washington State Emergency Management Division
- Course Instructor: [Professor Lenora Borchardt]
