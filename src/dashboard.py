import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point, box
import random

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Import custom modules
from live_weather_api import get_live_agricultural_risk
from roboflow_analyzer import analyze_roboflow_dataset

try:
    from satellite_analyzer import SatelliteAnalyzer
    SATELLITE_AVAILABLE = True
except ImportError:
    SATELLITE_AVAILABLE = False

# --- CONFIGURATION & REALISTIC ASSUMPTIONS ---
CROP_YIELDS = {"Rice": 3000, "Corn": 4500, "Cassava": 20000}
CAMBODIA_BOUNDS = {"lat_min": 10.0, "lat_max": 15.0, "lon_min": 102.0, "lon_max": 108.0}

st.set_page_config(page_title="FinUnity — Loan Assessment", layout="wide", page_icon="🌾")

# =============================================================================
# GLOBAL MATPLOTLIB STYLE
# =============================================================================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": True,
    "axes.grid": True,
    "grid.alpha": 0.15,
    "grid.color": "#C8C2B5",
    "grid.linestyle": ":",
    "figure.facecolor": "#FDFAF3",
    "axes.facecolor": "#FDFAF3",
    "text.color": "#2A241C",
    "axes.labelcolor": "#68635A",
    "axes.labelsize": 9,
    "xtick.color": "#9C9790",
    "ytick.color": "#9C9790",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.edgecolor": "#DDD7CB",
    "legend.frameon": True,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "#DDD7CB",
    "legend.fontsize": 8,
    "legend.facecolor": "#FDFAF3",
})

# =============================================================================
# CSS — Ledger Aesthetic
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:           #F4F0E6;
    --surface:      #FDFAF3;
    --surface-alt:  #F5F1E8;
    --border:       #DDD7CB;
    --border-light: #EAE5DB;
    --ink:          #1C1912;
    --ink-2:        #68635A;
    --ink-3:        #9C9790;
    --accent:       #4D7B5C;
    --accent-tint:  #EDF3EF;
    --amber:        #9B6A18;
    --amber-tint:   #F7F0E2;
    --red:          #8A2525;
    --red-tint:     #F5EDED;
    --mono:         'IBM Plex Mono', 'Courier New', monospace;
    --sans:         'IBM Plex Sans', system-ui, sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg);
    color: var(--ink);
}

.main .block-container {
    padding: 1.6rem 2.2rem 4rem 2.2rem;
    max-width: 1440px;
    background-color: var(--bg);
}

[data-testid="stSidebar"] {
    background-color: var(--surface);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.8rem;
}

[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] h3 {
    color: var(--ink-3);
    font-size: 0.68rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 1.4rem;
    margin-bottom: 0.5rem;
    font-family: var(--sans);
}

[data-testid="stSidebar"] .stButton > button {
    background-color: var(--accent);
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    font-size: 0.84rem;
    padding: 0.6rem 1.1rem;
    letter-spacing: 0.03em;
    font-family: var(--sans);
    width: 100%;
    cursor: pointer;
    transition: background-color 0.18s ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #3D6449;
}

.ledger-header {
    display: flex;
    align-items: flex-start;
    gap: 1.4rem;
    padding: 1.5rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.6rem;
}

.ledger-monogram {
    font-family: var(--mono);
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--ink-3);
    letter-spacing: 0.08em;
    line-height: 2.4;
    flex-shrink: 0;
}

.ledger-title {
    font-family: var(--sans);
    font-size: 1.55rem;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: -0.01em;
    line-height: 1.1;
    margin: 0;
}

.ledger-sub {
    font-size: 0.83rem;
    color: var(--ink-2);
    margin-top: 0.2rem;
}

.ledger-branch {
    margin-left: auto;
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--ink-3);
    text-align: right;
    line-height: 1.7;
}

.case-header {
    margin-bottom: 1.6rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-light);
}

.case-ref {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--ink-3);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}

.case-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 0.3rem 0;
}

.case-meta {
    font-size: 0.8rem;
    color: var(--ink-2);
    display: flex;
    gap: 1.4rem;
    flex-wrap: wrap;
}

.case-meta span::before {
    content: "·";
    margin-right: 0.5rem;
    color: var(--ink-3);
}

.case-meta span:first-child::before { content: ""; margin-right: 0; }

.section-header {
    display: flex;
    align-items: baseline;
    gap: 0.9rem;
    margin: 2.2rem 0 0.9rem 0;
    padding-bottom: 0.55rem;
    border-bottom: 1px solid var(--border);
}

.section-num {
    font-family: var(--mono);
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--ink-3);
    letter-spacing: 0.06em;
}

.section-header h3 {
    margin: 0;
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--ink);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-family: var(--sans);
}

[data-testid="metric-container"] {
    background: var(--surface);
    border-radius: 3px;
    padding: 0.9rem 1rem 0.8rem 1rem !important;
    border: 1px solid var(--border-light);
    transition: border-color 0.18s ease;
    min-height: 88px;
}

[data-testid="metric-container"]:hover {
    border-color: var(--border);
}

[data-testid="metric-container"] label {
    color: var(--ink-3) !important;
    font-size: 0.67rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: var(--sans) !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    font-family: var(--mono) !important;
}

[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.73rem !important;
    font-family: var(--mono) !important;
}

[data-testid="stSuccess"] {
    border-left: 3px solid var(--accent) !important;
    background-color: var(--accent-tint) !important;
}

[data-testid="stWarning"] {
    border-left: 3px solid var(--amber) !important;
    background-color: var(--amber-tint) !important;
}

[data-testid="stError"] {
    border-left: 3px solid var(--red) !important;
    background-color: var(--red-tint) !important;
}

[data-testid="stInfo"] {
    border-left: 3px solid var(--ink-3) !important;
    background-color: var(--surface-alt) !important;
}

.verdict-block {
    padding: 2rem 2.4rem;
    border: 1px solid var(--border);
    background: var(--surface);
    margin: 0.8rem 0 1.2rem 0;
}

.verdict-label {
    font-family: var(--mono);
    font-size: 0.67rem;
    font-weight: 500;
    color: var(--ink-3);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.5rem;
}

.verdict-text {
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.015em;
    line-height: 1;
    margin-bottom: 0.75rem;
    font-family: var(--sans);
}

.verdict-text.approve    { color: var(--accent); }
.verdict-text.conditional { color: var(--amber); }
.verdict-text.reject     { color: var(--red); }

.verdict-reason {
    font-size: 0.86rem;
    color: var(--ink-2);
    line-height: 1.6;
    max-width: 580px;
    margin-bottom: 1.4rem;
}

.verdict-terms {
    border-top: 1px solid var(--border-light);
    padding-top: 1rem;
}

.verdict-terms-label {
    font-family: var(--mono);
    font-size: 0.67rem;
    color: var(--ink-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.6rem;
}

.verdict-terms-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 0.6rem 2rem;
}

.verdict-term-item {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.verdict-term-key {
    font-size: 0.7rem;
    color: var(--ink-3);
    font-family: var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.verdict-term-val {
    font-size: 0.88rem;
    color: var(--ink);
    font-weight: 500;
    font-family: var(--mono);
}

.roi-section {
    background: var(--surface);
    border: 1px solid var(--border-light);
    padding: 0.9rem 1.1rem;
    margin-top: 0.5rem;
}

.roi-label {
    font-size: 0.67rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--ink-3);
    font-family: var(--mono);
    margin-bottom: 0.35rem;
}

.roi-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--ink);
    font-family: var(--mono);
    margin-bottom: 0.45rem;
}

.roi-bar-wrap {
    background: var(--border-light);
    height: 4px;
    overflow: hidden;
}

.roi-bar-fill {
    height: 100%;
    transition: width 0.5s ease;
}

.mitigation-box {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 1.1rem 1.3rem;
}

.mitigation-box-label {
    font-family: var(--mono);
    font-size: 0.67rem;
    color: var(--ink-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.7rem;
}

.mitigation-rule {
    font-size: 0.83rem;
    color: var(--ink-2);
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border-light);
    line-height: 1.5;
}

.mitigation-rule:last-child { border-bottom: none; }

.mitigation-rule strong { color: var(--ink); }

.audit-card {
    background: var(--surface);
    border: 1px solid var(--border-light);
    padding: 0.9rem 1rem;
    height: 100%;
    min-height: 120px;
}

.audit-title {
    font-family: var(--mono);
    font-size: 0.67rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--ink-3);
    margin-bottom: 0.45rem;
}

.audit-badge {
    display: inline-block;
    font-family: var(--mono);
    padding: 0.12rem 0.45rem;
    font-size: 0.68rem;
    font-weight: 500;
    margin-bottom: 0.45rem;
    letter-spacing: 0.04em;
}

.audit-badge.success { background: var(--accent-tint); color: var(--accent); }
.audit-badge.warning { background: var(--amber-tint);  color: var(--amber); }
.audit-badge.error   { background: var(--red-tint);    color: var(--red); }

.audit-detail {
    font-size: 0.78rem;
    color: var(--ink-2);
    line-height: 1.6;
}

.chart-wrap {
    background: var(--surface);
    border: 1px solid var(--border-light);
    padding: 0.3rem;
    overflow: hidden;
}

.loc-card {
    background: var(--surface);
    border: 1px solid var(--border-light);
    padding: 1.2rem 1.4rem;
}

.loc-card-label {
    font-family: var(--mono);
    font-size: 0.67rem;
    color: var(--ink-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.9rem;
}

.stDownloadButton > button {
    background-color: var(--ink) !important;
    color: var(--surface) !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: var(--sans) !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
}

.stDownloadButton > button:hover {
    background-color: var(--ink-2) !important;
}

hr {
    border: none;
    border-top: 1px solid var(--border-light);
    margin: 1.4rem 0;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# UI HELPER FUNCTIONS
# =============================================================================

def section_header(num: str, title: str):
    st.markdown(f"""
    <div class="section-header">
        <span class="section-num">§ {num}</span>
        <h3>{title}</h3>
    </div>
    """, unsafe_allow_html=True)


def decision_badge(verdict_class: str, text: str, reason: str, terms: dict | None = None):
    """Renders verdict using Streamlit native components"""
    
    # Color mapping
    colors = {
        "approve": ("#4D7B5C", "#EDF3EF"),
        "conditional": ("#9B6A18", "#F7F0E2"),
        "reject": ("#8A2525", "#F5EDED")
    }
    
    color, bg_color = colors.get(verdict_class, colors["conditional"])
    
    # Display verdict header
    st.markdown(f"""
    <div style="background:{bg_color};border-left:4px solid {color};
                padding:1.5rem;margin:1rem 0;border-radius:0 8px 8px 0;">
        <div style="font-family:'IBM Plex Mono';font-size:0.7rem;
                    text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--ink-3);margin-bottom:0.5rem;">Verdict</div>
        <div style="font-size:2rem;font-weight:600;color:{color};
                    margin-bottom:0.75rem;">{text}</div>
        <div style="font-size:0.86rem;color:var(--ink-2);
                    line-height:1.6;">{reason}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display terms if provided
    if terms:
        st.markdown("**Recommended terms:**")
        col1, col2 = st.columns(2)
        terms_list = list(terms.items())
        for i, (key, value) in enumerate(terms_list):
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"""
                <div style="margin-bottom:0.5rem;">
                    <div style="font-family:'IBM Plex Mono';
                                font-size:0.7rem;color:var(--ink-3);
                                text-transform:uppercase;">{key}</div>
                    <div style="font-family:'IBM Plex Mono';
                                font-size:0.88rem;color:var(--ink);
                                font-weight:500;">{value}</div>
                </div>
                """, unsafe_allow_html=True)


def roi_progress_bar(probability: float):
    if probability >= 80:
        bar_color = "var(--accent)"
    elif probability >= 60:
        bar_color = "var(--amber)"
    else:
        bar_color = "var(--red)"

    st.markdown(f"""
    <div class="roi-section">
        <div class="roi-label">Repayment probability</div>
        <div class="roi-value">{probability:.1f}%</div>
        <div class="roi-bar-wrap">
            <div class="roi-bar-fill"
                 style="width:{min(probability,100):.1f}%; background:{bar_color};">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def audit_card(col, title: str, badge_class: str, badge_label: str, detail: str):
    with col:
        st.markdown(f"""
        <div class="audit-card">
            <div class="audit-title">{title}</div>
            <span class="audit-badge {badge_class}">{badge_label}</span>
            <div class="audit-detail">{detail}</div>
        </div>
        """, unsafe_allow_html=True)


def dscr_table(rows: list):
    """Renders DSCR table using Streamlit native components"""
    # Create DataFrame for display
    df_data = []
    for r in rows:
        outcome_emoji = "✅" if r["outcome"] == "covered" else "⚠️" if r["outcome"] == "tight" else "❌"
        df_data.append({
            "Scenario": f"{r['name']} — {r['sub']}",
            "Revenue (USD)": f"${r['revenue']:,.0f}",
            "DSCR": f"{r['dscr']:.2f}×",
            "Outcome": f"{outcome_emoji} {r['outcome'].replace('-', ' ').title()}"
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Scenario": st.column_config.TextColumn("Scenario", width="large"),
            "Revenue (USD)": st.column_config.TextColumn("Revenue", width="medium"),
            "DSCR": st.column_config.TextColumn("DSCR", width="small"),
            "Outcome": st.column_config.TextColumn("Outcome", width="medium")
        }
    )


# =============================================================================
# LEDGER HEADER
# =============================================================================
st.markdown("""
<div class="ledger-header">
    <div class="ledger-monogram">F / U</div>
    <div style="flex:1;">
        <p class="ledger-title">FinUnity</p>
        <p class="ledger-sub">Agricultural credit assessment  ·  Rural Cambodia</p>
    </div>
    <div class="ledger-branch">
        AI-Powered Loan Risk Assessment<br>
        Branch B-04  ·  Battambang Region
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if 'map_lat' not in st.session_state:
    st.session_state['map_lat'] = 13.10
if 'map_lon' not in st.session_state:
    st.session_state['map_lon'] = 103.20

# =============================================================================
# SIDEBAR INPUTS
# =============================================================================
st.sidebar.markdown("### Application")
farmer_name = st.sidebar.text_input("Farmer name", "Sokhon Vichet")
province    = st.sidebar.selectbox("Province", ["Battambang", "Kampong Cham", "Takeo", "Prey Veng"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Location")
st.sidebar.caption("Click the map to select the farm location. Green overlays show verified farmland.")

m = folium.Map(
    location=[st.session_state['map_lat'], st.session_state['map_lon']],
    zoom_start=12,
    tiles='OpenStreetMap'
)

parquet_path = DATA_DIR / "field_boundaries" / "ai4sf.parquet"
if parquet_path.exists():
    try:
        import geopandas as gpd
        fields_gdf = gpd.read_parquet(parquet_path)

        if fields_gdf.crs and fields_gdf.crs.to_epsg() != 4326:
            fields_gdf = fields_gdf.to_crs(epsg=4326)

        bbox_min_lon = st.session_state['map_lon'] - 0.2
        bbox_max_lon = st.session_state['map_lon'] + 0.2
        bbox_min_lat = st.session_state['map_lat'] - 0.2
        bbox_max_lat = st.session_state['map_lat'] + 0.2

        bounding_box  = box(bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat)
        nearby_fields = fields_gdf[fields_gdf.geometry.intersects(bounding_box)]

        for idx, row in nearby_fields.iterrows():
            if row.geometry.geom_type == 'Polygon':
                coords = [(y, x) for x, y in row.geometry.exterior.coords]
                folium.Polygon(
                    locations=coords,
                    color='#4D7B5C', weight=2,
                    fill=True, fill_color='#4D7B5C', fill_opacity=0.18,
                    tooltip='Verified Farmland'
                ).add_to(m)

        st.sidebar.success(f"Loaded {len(nearby_fields)} farmland polygons nearby")
    except Exception as e:
        st.sidebar.warning(f"Could not load farmland boundaries: {e}")

folium.Marker(
    location=[st.session_state['map_lat'], st.session_state['map_lon']],
    popup="Selected Location",
    icon=folium.Icon(color='red', icon='info-sign')
).add_to(m)

map_data = st_folium(m, width=700, height=400, returned_objects=["last_clicked"])

if map_data and map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]
    st.session_state['map_lat'] = clicked_lat
    st.session_state['map_lon'] = clicked_lon
    st.sidebar.success(f"Selected: {clicked_lat:.4f}°N, {clicked_lon:.4f}°E")

st.sidebar.info(f"""
**Coordinates**
Latitude: {st.session_state['map_lat']:.4f}°N  
Longitude: {st.session_state['map_lon']:.4f}°E
""")

lat = st.session_state['map_lat']
lon = st.session_state['map_lon']

st.sidebar.markdown("---")
st.sidebar.markdown("### Crop & Loan")
crop_type   = st.sidebar.selectbox("Crop type", list(CROP_YIELDS.keys()))
hectares    = st.sidebar.number_input("Land area (ha)", value=2.0, min_value=0.1, step=0.1)
loan_amount = st.sidebar.number_input("Loan amount (USD)", value=500, min_value=100, step=100)

analyze_btn = st.sidebar.button("Run assessment", use_container_width=True)

# =============================================================================
# MAIN ANALYSIS BLOCK
# =============================================================================
if analyze_btn:

    if not (CAMBODIA_BOUNDS["lat_min"] <= lat <= CAMBODIA_BOUNDS["lat_max"] and
            CAMBODIA_BOUNDS["lon_min"] <= lon <= CAMBODIA_BOUNDS["lon_max"]):
        st.error(f"Invalid coordinates: ({lat}, {lon}) is outside Cambodia.")
        st.stop()

    with st.spinner("Analysing market, land, and satellite data..."):

        # =====================================================================
        # 1. MARKET SIMULATOR (WFP Data) — MULTI-TIER FALLBACK
        # =====================================================================
        market_data_loaded  = False
        market_verdict      = "REVIEW"
        current_price       = None
        predicted_mean      = None
        positive_roi_prob   = 0.0
        total_expected_yield = 0.0
        revenue_at_mean     = 0.0
        final_prices        = np.array([])

        try:
            file_path = DATA_DIR / "prices" / "wfp_food_prices_khm.csv"
            df        = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])

            rice_data = df[
                (df['commodity'].str.contains(crop_type, case=False, na=False)) &
                (df['admin1'].str.contains(province, case=False, na=False))
            ].sort_values('date').reset_index(drop=True)

            if rice_data.empty:
                st.warning(f"No provincial data for {crop_type} in {province}. Using national averages.")
                rice_data = df[
                    df['commodity'].str.contains(crop_type, case=False, na=False)
                ].sort_values('date').reset_index(drop=True)

            if rice_data.empty:
                st.warning(f"No data for {crop_type}. Using Rice as proxy commodity.")
                rice_data = df[
                    df['commodity'].str.contains('Rice', case=False, na=False)
                ].sort_values('date').reset_index(drop=True)

                yield_adjustment = {"Rice": 1.0, "Corn": 1.5, "Cassava": 6.7}
                CROP_YIELDS[crop_type] = int(CROP_YIELDS[crop_type] * yield_adjustment.get(crop_type, 1.0))

            if rice_data.empty:
                raise ValueError("No market data available for any crop.")

            if len(rice_data) < 10:
                st.error(f"Insufficient market data ({len(rice_data)} records). Minimum 10 required.")
                st.stop()

            current_price    = rice_data['usdprice'].iloc[-1]
            historical_mean  = rice_data['usdprice'].mean()
            historical_std   = rice_data['usdprice'].std()

            np.random.seed(42)
            n_simulations, n_days = 500, 180
            simulated_prices = np.zeros((n_simulations, n_days + 1))
            simulated_prices[:, 0] = current_price
            speed_of_reversion, volatility = 0.01, historical_std / np.sqrt(252)

            for i in range(n_simulations):
                current_price_sim = current_price
                for day in range(n_days):
                    drift = speed_of_reversion * (historical_mean - current_price_sim)
                    shock = volatility * np.random.normal()
                    current_price_sim = max(
                        0.01, current_price_sim + drift + (current_price_sim * shock)
                    )
                    simulated_prices[i, day + 1] = current_price_sim

            final_prices             = simulated_prices[:, -1]
            predicted_mean           = np.mean(final_prices)
            expected_yield_kg_per_ha = CROP_YIELDS[crop_type]
            total_expected_yield     = hectares * expected_yield_kg_per_ha
            revenue_at_mean          = total_expected_yield * predicted_mean
            
            # Calculate realistic ROI probability with operating costs
            operating_cost_rate = 0.40
            positive_roi_prob = (
                np.sum((final_prices * total_expected_yield * (1 - operating_cost_rate)) > loan_amount)
                / n_simulations
            ) * 100

            market_verdict     = ("APPROVE"  if positive_roi_prob >= 80
                                  else "REVIEW" if positive_roi_prob >= 60
                                  else "REJECT")
            market_data_loaded = True

        except Exception as e:
            st.error(f"Market data system failure — {e}")
            st.stop()

        # =====================================================================
        # 2. LAND RISK ANALYZER
        # =====================================================================
        land_data_loaded    = False
        pdsi_data_available = False
        drought_risk_score, flood_risk_score, viability_score = 50.0, 30.0, 60.0
        drought_years, flood_years, total_years = 0, 0, 0

        try:
            import geopandas as gpd
            shp_path = DATA_DIR / "flood_drought" / "Cambodia_Croplands.shp"

            if shp_path.exists():
                gdf       = gpd.read_file(shp_path)
                pdsi_cols = [col for col in gdf.columns if 'pdsi' in col.lower()]

                if pdsi_cols:
                    all_pdsi = []
                    for col in pdsi_cols:
                        all_pdsi.extend(gdf[col].dropna().values)
                    historical_pdsi = np.array(all_pdsi)

                    # Calculate realistic drought/flood years
                    drought_years = int(np.sum(historical_pdsi < -3.0))
                    flood_years   = int(np.sum(historical_pdsi >  3.0))
                    total_years   = len(historical_pdsi)

                    # Calculate risk scores as percentages
                    drought_risk_score = (
                        min(100, (drought_years / total_years) * 100) if total_years > 0 else 50.0
                    )
                    flood_risk_score   = (
                        min(100, (flood_years / total_years) * 100)   if total_years > 0 else 30.0
                    )
                    viability_score    = 100 - ((drought_risk_score + flood_risk_score) / 2)
                    pdsi_data_available = True
                    land_data_loaded    = True
                else:
                    st.warning("Shapefile loaded but PDSI columns missing.")
                    land_data_loaded = True
            else:
                st.error("Shapefile not found.")

        except Exception as e:
            st.error(f"Land analysis failed — {e}")

        land_verdict = (
            "APPROVED"            if viability_score >= 75
            else "REQUIRES INSURANCE" if viability_score >= 50
            else "REJECTED"
        )

        # =====================================================================
        # 3. FIELD BOUNDARY VERIFIER
        # =====================================================================
        is_in_farmland  = False
        is_in_agri_zone = False
        osm_data_loaded = False

        try:
            import geopandas as gpd
            farm_point = Point(lon, lat)

            if os.path.exists(parquet_path):
                fields_gdf = gpd.read_parquet(parquet_path)
                if fields_gdf.crs and fields_gdf.crs.to_epsg() != 4326:
                    fields_gdf = fields_gdf.to_crs(epsg=4326)

                is_in_farmland = fields_gdf.geometry.apply(
                    lambda g: g.contains(farm_point)
                ).any()
                if not is_in_farmland:
                    buffered_point = farm_point.buffer(0.01)
                    is_in_farmland = fields_gdf.geometry.apply(
                        lambda g: g.intersects(buffered_point)
                    ).any()
                osm_data_loaded = True

            if not is_in_farmland and os.path.exists(shp_path):
                croplands_gdf = gpd.read_file(shp_path)
                if croplands_gdf.crs and croplands_gdf.crs.to_epsg() != 4326:
                    croplands_gdf = croplands_gdf.to_crs(epsg=4326)
                is_in_agri_zone = croplands_gdf.geometry.apply(
                    lambda g: g.contains(farm_point)
                ).any()

        except Exception as e:
            st.warning(f"Field verification failed: {e}")

        # =====================================================================
        # 4. LIVE WEATHER API
        # =====================================================================
        live_weather_data = get_live_agricultural_risk(lat, lon)
        if live_weather_data.get("success"):
            if ("Flood"   in live_weather_data["live_risk_assessment"] or
                    "Drought" in live_weather_data["live_risk_assessment"]):
                land_verdict = "REQUIRES INSURANCE"

        # =====================================================================
        # 5. SATELLITE AI ANALYSIS (Qwen-VL)
        # =====================================================================
        ai_satellite_risk = "Unknown"
        if SATELLITE_AVAILABLE and os.getenv("QWEN_API_KEY"):
            try:
                satellite_base_dir = DATA_DIR / "satellite" / "rice_field_segmentation"
                sample_images = []
                if satellite_base_dir.exists():
                    for root, dirs, files in os.walk(satellite_base_dir):
                        for file in files:
                            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                                sample_images.append(os.path.join(root, file))
                                if len(sample_images) >= 5:
                                    break
                        if len(sample_images) >= 5:
                            break

                if sample_images:
                    analyzer  = SatelliteAnalyzer()
                    ai_result = analyzer.analyze_image(sample_images[0])
                    if "error" not in ai_result:
                        ai_satellite_risk               = ai_result.get("risk_level", "Unknown")
                        st.session_state['ai_analysis'] = ai_result
                        st.session_state['ai_image']    = sample_images[0]
            except Exception as e:
                st.warning(f"Satellite AI failed: {e}")

        # =====================================================================
        # 6. ROBOFLOW DATASET ANALYSIS
        # =====================================================================
        roboflow_results  = {}
        datasets_to_scan  = ['flood_detection', 'rice_field_segmentation']

        st.markdown("### Live processing log")
        st.caption("Scanning satellite imagery datasets...")

        for ds_name in datasets_to_scan:
            ds_label = ds_name.replace('_', ' ').title()
            st.markdown(f"**Scanning: {ds_label}**")
            try:
                roboflow_results[ds_name] = analyze_roboflow_dataset(ds_name, show_progress=True)
            except Exception as e:
                roboflow_results[ds_name] = {"error": str(e)}
            st.divider()

        # =====================================================================
        # DISPLAY DASHBOARD
        # =====================================================================

        case_ref = f"Application · {province[:2].upper()}-{datetime.now().strftime('%Y-%m%d')}"
        st.markdown(f"""
        <div class="case-header">
            <div class="case-ref">{case_ref}</div>
            <div class="case-title">{farmer_name} — {crop_type.lower()}, {hectares} ha</div>
            <div class="case-meta">
                <span>{datetime.now().strftime('%d %b %Y')}</span>
                <span>Province · {province}</span>
                <span>{lat:.4f}°N, {lon:.4f}°E</span>
                <span>Loan · USD {loan_amount:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if osm_data_loaded:
            if is_in_farmland:
                st.success("Location verified — coordinates fall within a mapped smallholder farm.")
            elif is_in_agri_zone:
                st.warning("Unmapped farm — location is within a verified agricultural zone.")
                land_verdict = "REQUIRES INSURANCE"
            else:
                st.error("Location failed — coordinates do not match any known farmland.")

        # ── § 01  Location Verification
        section_header("01", "Location Verification")
        st.caption("Verify ground-level conditions and road access.")

        col_street, col_sat = st.columns(2)

        with col_street:
            street_view_url = f"https://www.google.com/maps/@{lat},{lon},3a,75y,90t/data=!3m6!1e1!3m4!1s!2e0!7i16384!8i8192"
            st.markdown(f"""
            <div class='loc-card'>
                <div class='loc-card-label'>Street View — Google Maps</div>
                <p style="font-size:0.82rem;color:var(--ink-2);margin-bottom:0.9rem;">
                    View street-level imagery at the selected location.
                </p>
                <a href="{street_view_url}" target="_blank" rel="noopener noreferrer"
                   style="text-decoration:none;">
                    <button style="background:var(--ink);color:var(--surface);
                                   padding:0.5rem 1.1rem;border:none;
                                   font-family:var(--sans);font-size:0.82rem;
                                   font-weight:500;cursor:pointer;">
                        Open Street View
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)

        with col_sat:
            osm_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=18"
            google_sat_url = f"https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},16z/data=!3m1!1e3"
            st.markdown(f"""
            <div class='loc-card'>
                <div class='loc-card-label'>Satellite & Map View</div>
                <p style="font-size:0.82rem;color:var(--ink-2);margin-bottom:0.9rem;">
                    High-resolution imagery — field boundaries and access roads.
                </p>
                <div style="display:flex;gap:0.7rem;flex-wrap:wrap;">
                    <a href="{osm_url}" target="_blank" rel="noopener noreferrer"
                       style="text-decoration:none;">
                        <button style="background:var(--accent);color:#fff;
                                       padding:0.5rem 1rem;border:none;
                                       font-family:var(--sans);font-size:0.82rem;
                                       font-weight:500;cursor:pointer;">
                            OpenStreetMap
                        </button>
                    </a>
                    <a href="{google_sat_url}" target="_blank" rel="noopener noreferrer"
                       style="text-decoration:none;">
                        <button style="background:var(--surface-alt);color:var(--ink);
                                       padding:0.5rem 1rem;border:1px solid var(--border);
                                       font-family:var(--sans);font-size:0.82rem;
                                       font-weight:500;cursor:pointer;">
                            Google Satellite
                        </button>
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.info("Field agent checklist: road accessibility · proximity to markets · surrounding land use · water access.")

        # ── § 02  Key Risk Metrics
        section_header("02", "Key Risk Metrics")

        col1, col2, col3, col4, col5 = st.columns(5)

        if market_data_loaded:
            col1.metric(label="Market price", value=f"${current_price:.3f}")
            price_delta_pct = ((predicted_mean - current_price) / current_price) * 100 if current_price else 0
            col2.metric(label="6-month forecast", value=f"${predicted_mean:.3f}", delta=f"{price_delta_pct:+.1f}%")

        col3.metric(label="Drought risk", value=f"{drought_risk_score:.1f} / 100", 
                   delta=f"{drought_years} obs." if pdsi_data_available else "Estimated", delta_color="inverse")
        col4.metric(label="Land viability", value=f"{viability_score:.1f} / 100", 
                   delta="Viable" if viability_score >= 75 else "Marginal")

        if live_weather_data.get("success"):
            moisture_val = live_weather_data.get('soil_moisture')
            moisture_str = f"{moisture_val:.3f}" if moisture_val is not None else "N/A"
            col5.metric(label="Soil moisture", value=moisture_str, delta="Live")
        else:
            col5.metric("Weather API", "Failed", delta="Check connection", delta_color="inverse")

        # ── § 03  Live Environmental Conditions
        if live_weather_data.get("success"):
            section_header("03", "Live Environmental Conditions")
            live_col1, live_col2, live_col3 = st.columns(3)
            live_col1.metric("Rainfall (current)", f"{live_weather_data['current_rain']} mm")
            live_col2.metric("7-day rain forecast", f"{live_weather_data['7_day_rain_forecast']} mm")
            live_col3.metric("Live risk assessment", live_weather_data['live_risk_assessment'])

            if live_weather_data['risk_color'] != 'green':
                st.error(f"Live alert — {live_weather_data['live_risk_assessment']} detected.")

        # ── § 04  Price and Land Signals
        section_header("04", "Price and Land Signals")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.caption("Farm-gate price forecast · 6-month horizon · Monte Carlo 500 simulations")
            if market_data_loaded:
                fig, ax = plt.subplots(figsize=(8, 3.8))
                ax.plot(rice_data['date'], rice_data['usdprice'], color='#4D7B5C', linewidth=1.8, label='Historical')
                days = np.arange(n_days + 1)
                ax.plot(days + len(rice_data), np.mean(simulated_prices, axis=0), color='#9B6A18', linewidth=2.0, label='Forecast', linestyle='--')
                ax.fill_between(days + len(rice_data), np.percentile(simulated_prices, 2.5, axis=0), 
                               np.percentile(simulated_prices, 97.5, axis=0), alpha=0.1, color='#9B6A18', label='95% CI')
                ax.set_ylabel("USD / kg", fontsize=8)
                ax.legend(loc='upper left', fontsize=8)
                fig.tight_layout(pad=0.8)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

        with chart_col2:
            st.caption("Land risk breakdown · Historical drought and flood frequency")
            fig, ax = plt.subplots(figsize=(8, 3.8))
            risks = ['Drought risk', 'Flood risk']
            scores = [drought_risk_score, flood_risk_score]
            colors = ['#8A2525' if s > 50 else '#9B6A18' if s > 25 else '#4D7B5C' for s in scores]
            bars = ax.barh(risks, scores, color=colors, height=0.45)
            ax.set_xlim(0, 110)
            ax.set_xlabel("Score (0–100)", fontsize=8)
            for bar, v in zip(bars, scores):
                ax.text(v + 1.5, bar.get_y() + bar.get_height() / 2, f"{v:.1f}", va='center', fontweight='600', fontsize=10)
            ax.axvline(50, color='#9C9790', linewidth=0.8, linestyle=':', label='Threshold')
            ax.legend(fontsize=8)
            fig.tight_layout(pad=0.8)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        # ── § 05  Satellite Analysis
        if 'ai_analysis' in st.session_state and 'ai_image' in st.session_state:
            section_header("05", "Satellite Analysis")
            col_img, col_data = st.columns([1, 2])
            with col_img:
                st.image(st.session_state['ai_image'], caption="Sample satellite view", width=300)
            with col_data:
                st.json(st.session_state['ai_analysis'])
                if st.session_state['ai_analysis'].get("risk_level") == "High":
                    st.error("High risk detected in satellite imagery.")

        # ── § 06  Roboflow Dataset Analysis
        section_header("06", "Roboflow Dataset Analysis")
        st.caption("Vegetation and water coverage statistics from satellite imagery.")

        for ds_name, ds_result in roboflow_results.items():
            ds_label = ds_name.replace('_', ' ').title()
            st.markdown(f"**{ds_label}**")

            if ds_result.get("success"):
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Total images", f"{ds_result['total_images_available']}")
                col_b.metric("Images scanned", ds_result['images_scanned'])
                col_c.metric("Avg vegetation", f"{ds_result['avg_vegetation_coverage']}%")
                col_d.metric("Avg water / flood", f"{ds_result['avg_water_coverage']}%")

                if ds_name == 'flood_detection' and ds_result['avg_water_coverage'] > 10:
                    st.warning(f"{ds_label} shows {ds_result['avg_water_coverage']}% water coverage — elevated flood risk.")
                    if ds_result['avg_water_coverage'] > 20:
                        land_verdict = "REQUIRES INSURANCE"
                elif ds_name == 'rice_field_segmentation' and ds_result['avg_vegetation_coverage'] > 40:
                    st.success(f"{ds_result['avg_vegetation_coverage']}% vegetation coverage — good agricultural conditions.")
                else:
                    st.info(f"{ds_result['risk_assessment']}")
            else:
                st.error(f"Could not scan {ds_label}: {ds_result.get('error')}")

        # ── § 07  Stress Test & Scenario Analysis
        section_header("07", "Stress Test & Scenario Analysis")
        st.caption("Loan viability under adverse conditions. DSCR = net revenue / loan payment.")

        if market_data_loaded and len(final_prices) > 0:
            # REALISTIC OPERATING COSTS (40% of revenue for rice farming)
            operating_cost_rate = 0.40
            operating_costs = revenue_at_mean * operating_cost_rate
            net_revenue_baseline = revenue_at_mean - operating_costs
            
            # Dynamic loan sizing
            conservative_price = np.percentile(final_prices, 25)
            conservative_revenue = total_expected_yield * conservative_price
            conservative_net = conservative_revenue - (conservative_revenue * operating_cost_rate)
            max_safe_loan = conservative_net * 0.70

            if viability_score < 60:
                max_safe_loan *= 0.80

            if loan_amount > max_safe_loan:
                st.error(f"Loan exceeds safe limit. Requested: **USD {loan_amount:,}** · Maximum safe: **USD {max_safe_loan:,.0f}**")
                market_verdict = "REJECT"

            # REALISTIC DSCR CALCULATIONS WITH COSTS
            scenarios_def = [
                {"name": "Baseline", "sub": "Forecast prices, expected yield", "price_mult": 1.0, "yield_mult": 1.0},
                {"name": "Price shock −25%", "sub": "Market oversupply", "price_mult": 0.75, "yield_mult": 1.0},
                {"name": "Yield shock −35%", "sub": "Severe drought/pest", "price_mult": 1.0, "yield_mult": 0.65},
                {"name": "Combined crisis", "sub": "Price −25% and yield −35%", "price_mult": 0.75, "yield_mult": 0.65},
            ]

            dscr_rows = []
            for s in scenarios_def:
                stressed_price = predicted_mean * s["price_mult"]
                stressed_yield = total_expected_yield * s["yield_mult"]
                gross_revenue = stressed_yield * stressed_price
                stressed_costs = gross_revenue * operating_cost_rate
                net_revenue = gross_revenue - stressed_costs
                
                # DSCR = net revenue / annual loan payment
                dscr = net_revenue / loan_amount if loan_amount > 0 else 0
                
                # MORE STRINGENT OUTCOME DETERMINATION
                if dscr >= 1.25:
                    outcome = "covered"
                elif dscr >= 1.0:
                    outcome = "tight"
                else:
                    outcome = "at-risk"
                
                dscr_rows.append({
                    "name": s["name"],
                    "sub": s["sub"],
                    "revenue": net_revenue,
                    "dscr": dscr,
                    "outcome": outcome,
                })

            stress_col1, stress_col2 = st.columns([3, 2])

            with stress_col1:
                dscr_table(dscr_rows)

            with stress_col2:
                # Calculate realistic ROI with costs
                net_roi_prob = (
                    np.sum((final_prices * total_expected_yield * (1 - operating_cost_rate)) > loan_amount)
                    / n_simulations
                ) * 100
                
                if net_roi_prob < 70:
                    rule_text, rule_color = "High risk — require collateral.", "var(--red)"
                elif net_roi_prob < 85:
                    rule_text, rule_color = "Moderate risk — mandatory insurance.", "var(--amber)"
                else:
                    rule_text, rule_color = "Acceptable risk — standard terms.", "var(--accent)"

                st.markdown(f"""
                <div class="mitigation-box">
                    <div class="mitigation-box-label">FSP risk mitigation</div>
                    <div class="mitigation-rule" style="color:{rule_color};"><strong>Assessment:</strong> {rule_text}</div>
                    <div class="mitigation-rule"><strong>Operating costs:</strong> {operating_cost_rate*100:.0f}% of gross revenue (seeds, labor, fertilizer)</div>
                    <div class="mitigation-rule"><strong>Portfolio rule:</strong> Max 20% exposure per province/crop.</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # ── § 08  Recommendation
        section_header("08", "Recommendation")

        if market_verdict == "REJECT" or land_verdict == "REJECTED" or ai_satellite_risk == "High":
            final_rec, verdict_class = "Reject", "reject"
            rec_reason = "Application fails safety thresholds across market, land, or satellite analysis."
        elif market_verdict == "APPROVE" and land_verdict == "APPROVED" and ai_satellite_risk in ["Low", "Unknown"]:
            final_rec, verdict_class = "Approve", "approve"
            rec_reason = "Market conditions, land history, and satellite imagery are favourable."
        else:
            final_rec, verdict_class = "Conditional Approval", "conditional"
            rec_reason = f"Requires {land_verdict.lower()} or further manual review."

        rec_terms = None
        if market_data_loaded:
            rec_terms = {
                "Principal": f"USD {loan_amount:,}",
                "Term": "10 months",
                "First payment": "After harvest",
                "ROI prob.": f"{positive_roi_prob:.1f}%",
                "Land verdict": land_verdict.lower(),
            }

        decision_badge(verdict_class, final_rec, rec_reason, rec_terms)

        if market_data_loaded:
            roi_col, proj_col = st.columns([1, 2])
            with roi_col:
                roi_progress_bar(positive_roi_prob)
            with proj_col:
                st.success(f"Expected yield: **{total_expected_yield:,.0f} kg** · Revenue: **USD {revenue_at_mean:,.2f}** · Repayment probability: **{positive_roi_prob:.1f}%**")

        # ── § 09  Data Transparency & Audit Trail
        section_header("09", "Data Transparency & Audit Trail")

        a1, a2, a3, a4 = st.columns(4)

        if market_data_loaded:
            audit_card(a1, "Market data", "success", "Loaded", 
                      f"Records: <strong>{len(rice_data):,}</strong><br>Period: {rice_data['date'].min().year}–{rice_data['date'].max().year}<br>Source: WFP KHM CSV")
        else:
            audit_card(a1, "Market data", "error", "Failed", "Could not load WFP price data.")

        if pdsi_data_available:
            audit_card(a2, "Land data", "success", "Loaded", 
                      f"PDSI points: <strong>{total_years:,}</strong><br>Drought obs: {drought_years}<br>Source: Cambodia Croplands SHP")
        else:
            audit_card(a2, "Land data", "warning", "Fallback", "Shapefile loaded — PDSI columns missing.")

        if osm_data_loaded:
            if is_in_farmland:
                audit_card(a3, "Field boundaries", "success", "Exact match", "Source: AI4SmallFarms Parquet<br>Verification: Exact polygon match")
            elif is_in_agri_zone:
                audit_card(a3, "Field boundaries", "warning", "Regional zone", "Source: Croplands Grid<br>Verification: Regional agricultural zone")
            else:
                audit_card(a3, "Field boundaries", "error", "No match", "Source: AI4SmallFarms Parquet<br>Verification: No matching polygon")
        else:
            audit_card(a3, "Field boundaries", "error", "Skipped", "GeoParquet file not found.")

        total_rf_images = sum(r.get('total_images_available', 0) for r in roboflow_results.values() if r.get('success'))
        n_rf_success = len([r for r in roboflow_results.values() if r.get('success')])

        if n_rf_success > 0:
            audit_card(a4, "Roboflow datasets", "success", "Loaded", 
                      f"Total images: <strong>{total_rf_images:,}</strong><br>Datasets scanned: {n_rf_success}<br>Sources: flood_detection, rice_seg")
        else:
            audit_card(a4, "Roboflow datasets", "error", "Failed", "No datasets could be scanned.")

        # ── § 10  Save & Export
        section_header("10", "Save & Export Application")

        report_data = {
            'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'Farmer Name': [farmer_name],
            'Province': [province],
            'Latitude': [f"{lat:.4f}"],
            'Longitude': [f"{lon:.4f}"],
            'Crop Type': [crop_type],
            'Land Area (ha)': [hectares],
            'Loan Amount (USD)': [loan_amount],
            'Final Decision': [final_rec],
            'ROI Probability (%)': [f"{positive_roi_prob:.1f}"],
            'Land Viability Score': [f"{viability_score:.1f}"],
            'Market Verdict': [market_verdict],
            'Land Verdict': [land_verdict]
        }
        report_df = pd.DataFrame(report_data)
        csv = report_df.to_csv(index=False).encode('utf-8')

        exp_col1, exp_col2 = st.columns([1, 2])
        with exp_col1:
            st.download_button(label="Download assessment report (CSV)", data=csv,
                             file_name=f"FinUnity_{farmer_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                             mime="text/csv", use_container_width=True)
        with exp_col2:
            csv_file_path = BASE_DIR / "outputs" / "loan_applications.csv"
            csv_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_exists = csv_file_path.exists()
            report_df.to_csv(csv_file_path, mode='a', header=not file_exists, index=False)
            st.success(f"Application saved to local database — `{csv_file_path.name}`")