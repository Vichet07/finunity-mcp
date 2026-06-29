import folium
from folium.plugins import Draw
import geopandas as gpd
import os
import json
from streamlit_folium import st_folium

def create_interactive_map(default_lat=13.10, default_lon=103.20):
    """
    Creates an interactive Folium map with:
    - Click-to-select coordinates
    - Farmland boundary overlay (if available)
    - Cambodia basemap
    """
    # Create base map centered on Cambodia
    m = folium.Map(
        location=[default_lat, default_lon],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add farmland boundaries from AI4SmallFarms
    parquet_path = 'data/field_boundaries/ai4sf.parquet'
    if os.path.exists(parquet_path):
        try:
            fields_gdf = gpd.read_parquet(parquet_path)
            
            # Convert to EPSG:4326 if needed
            if fields_gdf.crs and fields_gdf.crs.to_epsg() != 4326:
                fields_gdf = fields_gdf.to_crs(epsg=4326)
            
            # Filter to show only boundaries near the default location (within 0.5 degrees)
            bbox = gpd.GeoDataFrame(
                geometry=[folium.LatLng(default_lat - 0.5, default_lon - 0.5),
                         folium.LatLng(default_lat + 0.5, default_lon + 0.5)]
            )
            nearby_fields = fields_gdf[
                fields_gdf.geometry.intersects(
                    gpd.box(default_lon - 0.5, default_lat - 0.5, 
                           default_lon + 0.5, default_lat + 0.5)
                )
            ]
            
            # Add farmland polygons to map (green outline)
            for _, row in nearby_fields.iterrows():
                if row.geometry.geom_type == 'Polygon':
                    folium.Polygon(
                        locations=[(y, x) for x, y in row.geometry.exterior.coords],
                        color='green',
                        weight=2,
                        fill=True,
                        fill_color='green',
                        fill_opacity=0.1,
                        tooltip='Verified Farmland'
                    ).add_to(m)
                    
        except Exception as e:
            print(f"Could not load farmland boundaries: {e}")
    
    # Add a marker at the default location
    folium.Marker(
        location=[default_lat, default_lon],
        popup="Selected Location",
        icon=folium.Icon(color='red', icon='map-marker')
    ).add_to(m)
    
    return m

def display_map_with_selection():
    """
    Display interactive map in Streamlit and return selected coordinates
    """
    st.markdown("### 🗺️ Interactive Location Selector")
    st.markdown("*Click anywhere on the map to select farm location. Green areas indicate verified farmland from AI4SmallFarms database.*")
    
    # Get default coordinates from session state or use Battambang
    default_lat = st.session_state.get('map_lat', 13.10)
    default_lon = st.session_state.get('map_lon', 103.20)
    
    # Create map
    m = create_interactive_map(default_lat, default_lon)
    
    # Display map with click functionality
    map_data = st_folium(
        m,
        width=800,
        height=500,
        returned_objects=["last_clicked"]
    )
    
    # Update coordinates if user clicked on map
    if map_data and map_data.get("last_clicked"):
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]
        
        st.session_state['map_lat'] = clicked_lat
        st.session_state['map_lon'] = clicked_lon
        
        st.success(f"📍 Selected: {clicked_lat:.4f}°N, {clicked_lon:.4f}°E")
        
        return clicked_lat, clicked_lon
    
    return default_lat, default_lon