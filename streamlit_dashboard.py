"""
Washington Climate-Fire Risk Intelligence Dashboard
ENHANCED VERSION with FEMA Disaster Markers

Features:
- Base choropleth by risk score
- Individual FEMA disaster markers
- Combined FEMA + NOAA statistics
- Interactive popups with fire history

Author: Josh Curry
Course: EM440 -  Geographic Information Systems (GIS) for EM - Professor Borchardt  
Date: November 4, 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium import plugins
from streamlit_folium import folium_static
import json

# Page configuration
st.set_page_config(
    page_title="WA Climate-Fire Risk Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #1976d2;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stMetric label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #263238 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: bold !important;
        color: #c62828 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("🔥 Washington Climate-Fire Risk Intelligence Dashboard")
st.subheader("EM440: Geographic Information Systems (GIS) for EM - Module 7 - Josh Curry")
st.markdown("**2019-2024 Climate Trends & Historical Fire Analysis**")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    """Load the integrated dashboard dataset"""
    df = pd.read_csv('data/WA_Climate_Fire_Dashboard_Data.csv')
    return df

@st.cache_data
def load_fema_data():
    """Load FEMA disaster data"""
    try:
        fema = pd.read_csv('data/FEMA_Disasters_Geocoded.csv')
        fema['declarationDate'] = pd.to_datetime(fema['declarationDate'])
        return fema
    except FileNotFoundError:
        return None

@st.cache_data
def load_geojson():
    """Load Washington counties GeoJSON"""
    with open('data/wa_counties.geojson', 'r') as f:
        geojson = json.load(f)
    return geojson

try:
    df = load_data()
    geojson = load_geojson()
    fema_data = load_fema_data()
except FileNotFoundError:
    st.error("⚠️ Data files not found. Please ensure data/ folder contains required files.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Controls")

# Risk category filter
risk_categories = ['All'] + sorted(df['risk_category'].unique().tolist())
selected_risk = st.sidebar.selectbox("Risk Category", risk_categories, index=0)

# Climate trend filter
climate_trends = ['All'] + sorted(df['climate_trend'].unique().tolist())
selected_trend = st.sidebar.selectbox("Climate Trend", climate_trends, index=0)

# Population threshold
min_population = st.sidebar.slider(
    "Minimum County Population",
    min_value=0,
    max_value=int(df['population'].max()),
    value=0,
    step=10000
)

# FEMA markers toggle
show_fema_markers = st.sidebar.checkbox("Show FEMA Disaster Markers", value=True)

if show_fema_markers and fema_data is not None:
    fema_year_range = st.sidebar.slider(
        "FEMA Disasters Year Range",
        min_value=int(fema_data['declarationDate'].dt.year.min()),
        max_value=int(fema_data['declarationDate'].dt.year.max()),
        value=(2015, int(fema_data['declarationDate'].dt.year.max()))
    )

# Apply filters
filtered_df = df.copy()
if selected_risk != 'All':
    filtered_df = filtered_df[filtered_df['risk_category'] == selected_risk]
if selected_trend != 'All':
    filtered_df = filtered_df[filtered_df['climate_trend'] == selected_trend]
filtered_df = filtered_df[filtered_df['population'] >= min_population]

st.sidebar.markdown("---")
st.sidebar.info(f"**{len(filtered_df)}** of {len(df)} counties shown")

# Key metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "High Risk Counties",
        len(df[df['risk_category'] == 'High']),
        help="Counties with risk scores 55-100"
    )

with col2:
    fema_count = len(fema_data) if fema_data is not None else 211
    st.metric(
        "FEMA Fire Disasters",
        fema_count,
        help="Federal disaster declarations 1991-2024"
    )

with col3:
    st.metric(
        "WUI Population",
        f"{df['population'].sum() / 1000000:.1f}M",
        help="People in WUI census blocks"
    )

with col4:
    wui_pct = (df['population_at_risk'].sum() / df['population'].sum() * 100)
    st.metric(
        "High WUI Risk",
        f"{df['population_at_risk'].sum() / 1000000:.1f}M ({wui_pct:.0f}%)",
        help="Interface/Intermix weighted population"
    )

st.markdown("---")

# Add data source info
if fema_data is not None:
    st.info(f"""
    📊 **Multi-Source Fire Data**: This dashboard combines {len(fema_data)} FEMA disaster declarations 
    (1991-2024) with 482 NOAA wildfire events (1996-2024) and climate trend analysis to provide 
    comprehensive fire risk intelligence for mitigation planning.
    """)

# Map and charts layout
map_col, chart_col = st.columns([2.5, 1])

with map_col:
    st.subheader("📍 Interactive Multi-Layer Risk Map")
    
    # Dynamic caption
    if selected_trend == 'Stable' and selected_risk == 'All':
        st.caption("⚠️ Showing 'Stable' climate counties. Risk scores may still be elevated due to fire history or WUI exposure.")
    elif selected_trend == 'Warming & Drying':
        st.caption("🌡️ Showing counties with both warming and drying trends - highest climate concern.")
    elif selected_risk == 'High':
        st.caption("🔴 Showing high-risk counties (scores 55-100) regardless of climate trend.")
    else:
        st.caption("Counties colored by Climate-Fire Risk Score. Toggle layers to show FEMA disasters.")
    
    # Create base map
    m = folium.Map(
        location=[47.5, -120.5],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Determine color scheme
    if selected_trend == 'Warming & Drying':
        color_scheme = 'Reds'
        fill_opacity = 0.8
    elif selected_trend == 'Stable':
        color_scheme = 'Greens'
        fill_opacity = 0.6
    elif selected_risk == 'Low':
        color_scheme = 'Greens'
        fill_opacity = 0.6
    else:
        color_scheme = 'YlOrRd'
        fill_opacity = 0.7
    
    # Add choropleth layer
    folium.Choropleth(
        geo_data=geojson,
        name='Risk Score',
        data=filtered_df,
        columns=['county_fips', 'climate_fire_risk_score'],
        key_on='feature.properties.GEOID',
        fill_color=color_scheme,
        fill_opacity=fill_opacity,
        line_opacity=0.3,
        legend_name='Climate-Fire Risk Score',
        nan_fill_color='lightgray'
    ).add_to(m)
    
    # Add FEMA disaster markers
    if show_fema_markers and fema_data is not None:
        fema_filtered = fema_data[
            (fema_data['declarationDate'].dt.year >= fema_year_range[0]) &
            (fema_data['declarationDate'].dt.year <= fema_year_range[1])
        ]
        
        # Only show disasters with valid coordinates
        fema_filtered = fema_filtered.dropna(subset=['lat', 'lon'])
        
        # Create marker cluster for FEMA disasters
        marker_cluster = plugins.MarkerCluster(name='FEMA Disasters').add_to(m)
        
        # Add individual markers (now with CORRECT coordinates)
        for idx, row in fema_filtered.iterrows():
            popup_html = f"""
            <div style="font-family: Arial; width: 250px;">
                <h4 style="margin: 0; color: #c62828;">🏛️ FEMA Disaster</h4>
                <hr style="margin: 5px 0;">
                <b>{row['declarationTitle']}</b><br>
                <b>County:</b> {row['County']}<br>
                <b>Date:</b> {row['declarationDate'].strftime('%Y-%m-%d')}<br>
                <b>Disaster #:</b> {row['disasterNumber']}<br>
                <hr style="margin: 5px 0;">
                <small>Federal assistance required<br>
                Location: County centroid</small>
            </div>
            """
            
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=row['declarationTitle'],
                icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon')
            ).add_to(marker_cluster)
    
    # Add enhanced county popups
    for _, row in filtered_df.iterrows():
        # Find matching feature in geojson
        for feature in geojson['features']:
            if feature['properties']['GEOID'] == str(int(row['county_fips'])):
                # Count FEMA disasters for this county
                if fema_data is not None:
                    county_fema = fema_data[fema_data['County'] == row['County']]
                    fema_count_county = len(county_fema)
                    recent_fires = county_fema.sort_values('declarationDate', ascending=False).head(3)
                    fires_list = '<br>'.join([
                        f"• {fire['declarationTitle']} ({fire['declarationDate'].strftime('%Y')})"
                        for _, fire in recent_fires.iterrows()
                    ])
                else:
                    fema_count_county = 0
                    fires_list = "Data not available"
                
                popup_html = f"""
                <div style="font-family: Arial; width: 300px;">
                    <h3 style="margin: 0; color: #1976d2;">{row['County']} County</h3>
                    <hr style="margin: 5px 0;">
                    <b>Risk Score:</b> {row['climate_fire_risk_score']:.1f} ({row['risk_category']})<br>
                    <b>Climate Trend:</b> {row['climate_trend']}<br>
                    <hr style="margin: 5px 0;">
                    <h4 style="margin: 5px 0;">🏛️ Federal Disasters: {fema_count_county}</h4>
                    <b>Population:</b> {row['population']:,}<br>
                    <b>At Risk:</b> {row['population_at_risk']:,.0f} ({row['wui_exposure_pct']:.1f}% WUI)<br>
                    <hr style="margin: 5px 0;">
                    <b>Recent Major Fires:</b><br>
                    {fires_list}
                </div>
                """
                
                # Use polygon centroid for marker
                folium.Marker(
                    location=[
                        float(feature['properties'].get('INTPTLAT', 47.5)),
                        float(feature['properties'].get('INTPTLON', -120.5))
                    ],
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=f"{row['County']}: {row['climate_fire_risk_score']:.1f}",
                    icon=folium.Icon(
                        color='darkred' if row['risk_category'] == 'High' else 
                              'orange' if row['risk_category'] == 'Moderate' else 'green',
                        icon='info-sign'
                    )
                ).add_to(m)
                break
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Display map
    folium_static(m, width=900, height=600)

with chart_col:
    st.subheader("📊 Risk Distribution")
    
    # Risk pie chart
    risk_counts = filtered_df['risk_category'].value_counts()
    fig_pie = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        color=risk_counts.index,
        color_discrete_map={
            'Critical': '#8B0000',
            'High': '#FF4500',
            'Moderate': '#FFA500',
            'Low': '#90EE90'
        }
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.subheader("🌡️ Climate Trends")
    
    # Climate trend bar chart
    trend_counts = filtered_df['climate_trend'].value_counts()
    fig_bar = px.bar(
        x=trend_counts.index,
        y=trend_counts.values,
        labels={'x': 'Trend Type', 'y': 'County Count'},
        color=trend_counts.values,
        color_continuous_scale='Reds'
    )
    fig_bar.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# County rankings table
st.subheader("🎯 County Risk Rankings with Fire History")

display_cols = ['County', 'climate_fire_risk_score', 'risk_category', 'climate_trend', 
                'population_at_risk', 'wui_exposure_pct']

display_df = filtered_df[display_cols].copy()

# Add FEMA count if available
if fema_data is not None:
    fema_counts = fema_data.groupby('County').size().reset_index(name='FEMA_Disasters')
    display_df = display_df.merge(fema_counts, on='County', how='left')
    display_df['FEMA_Disasters'] = display_df['FEMA_Disasters'].fillna(0).astype(int)
    
    display_df.columns = ['County', 'Risk Score', 'Category', 'Climate Trend', 
                          'Population at Risk', 'WUI %', 'Federal Disasters']
else:
    display_df.columns = ['County', 'Risk Score', 'Category', 'Climate Trend', 
                          'Population at Risk', 'WUI %']

# Format
display_df['Risk Score'] = display_df['Risk Score'].round(1)
display_df['Population at Risk'] = display_df['Population at Risk'].apply(lambda x: f"{x:,.0f}")
display_df['WUI %'] = display_df['WUI %'].round(1)

# Add ranking
display_df.insert(0, 'Rank', range(1, len(display_df) + 1))

st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv,
    file_name="wa_climate_fire_risk_filtered.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.markdown("""
    **Data Sources:** 
    • Climate: NOAA Climate Normals (2019-2024)  
    • Fire Disasters: FEMA Declarations (1991-2024) & NOAA Storm Events (1996-2024)  
    • Wildland-Urban Interface: USDA Forest Service  
    • Demographics: U.S. Census Bureau  
    
    **Last Updated:** November 2025 | Washington State Emergency Management
""")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("""
    ### 🎯 About This Dashboard
    
    Multi-layer fire risk analysis combining:
    - **186 FEMA disasters** (1991-2024)
    - **482 NOAA wildfire events** (1996-2024)
    - **Climate trends** (2019-2024)
    - **Wildland-Urban Interface (WUI) exposure** data
    
    **Mission Areas:**
    - Mitigation (primary)
    - Preparedness (secondary)
    
    Toggle FEMA markers to see individual 
    disaster locations and details.
""")
