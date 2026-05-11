"""
GIS analysis: catchment areas, nearest-facility distance, and underserved zone mapping.
"""
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium.plugins import MarkerCluster
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import generate_facilities, generate_health_gaps, STATES


def build_facility_gdf(facilities_df: pd.DataFrame) -> gpd.GeoDataFrame:
    geom = [Point(r.lon, r.lat) for _, r in facilities_df.iterrows()]
    return gpd.GeoDataFrame(facilities_df, geometry=geom, crs="EPSG:4326")


def build_state_gdf(gaps_df: pd.DataFrame) -> gpd.GeoDataFrame:
    geom = [Point(r.lon, r.lat) for _, r in gaps_df.iterrows()]
    return gpd.GeoDataFrame(gaps_df, geometry=geom, crs="EPSG:4326")


def compute_nearest_facility(state_gdf: gpd.GeoDataFrame,
                              facility_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    state_m = state_gdf.to_crs("EPSG:32632")
    facility_m = facility_gdf[facility_gdf["operational"] == True].to_crs("EPSG:32632")
    state_m["nearest_facility_km"] = state_m.geometry.apply(
        lambda pt: facility_m.geometry.distance(pt).min() / 1000
    )
    return state_m.to_crs("EPSG:4326")


def build_catchment_buffers(facility_gdf: gpd.GeoDataFrame,
                             radius_km: float = 10) -> gpd.GeoDataFrame:
    facility_m = facility_gdf[facility_gdf["operational"] == True].to_crs("EPSG:32632").copy()
    facility_m["catchment"] = facility_m.geometry.buffer(radius_km * 1000)
    return facility_m.set_geometry("catchment").to_crs("EPSG:4326")


def build_access_map(state_gdf: gpd.GeoDataFrame,
                     facility_gdf: gpd.GeoDataFrame) -> folium.Map:
    m = folium.Map(location=[9.08, 8.67], zoom_start=6, tiles="CartoDB positron")

    cluster = MarkerCluster(name="Health Facilities").add_to(m)

    type_colors = {
        "Teaching Hospital": "red", "General Hospital": "blue",
        "Primary Health Centre": "green", "Specialist Clinic": "purple",
        "Private Hospital": "orange", "Maternity Centre": "pink",
    }
    for _, row in facility_gdf[facility_gdf["operational"] == True].head(300).iterrows():
        color = type_colors.get(row["type"], "gray")
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color=color, fill=True, fill_opacity=0.8,
            popup=f"<b>{row['name']}</b><br>Type: {row['type']}<br>Beds: {row['beds']}<br>Doctors: {row['doctors']}",
            tooltip=row["type"],
        ).add_to(cluster)

    # State gap overlay
    for _, row in state_gdf.iterrows():
        gap = row.get("gap_score", 0.5)
        color = "#d32f2f" if gap > 0.6 else "#f57c00" if gap > 0.4 else "#388e3c"
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=max(8, gap * 30),
            color=color, fill=True, fill_opacity=0.35,
            popup=f"<b>{row['state']}</b><br>Coverage: {100 - row['gap_score']*100:.0f}%<br>"
                  f"Travel time: {row['avg_travel_time_min']:.0f} min",
            tooltip=row["state"],
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


if __name__ == "__main__":
    fac_df = generate_facilities()
    gap_df = generate_health_gaps()
    fac_gdf = build_facility_gdf(fac_df)
    state_gdf = build_state_gdf(gap_df)
    m = build_access_map(state_gdf, fac_gdf)
    os.makedirs("app", exist_ok=True)
    m.save("app/healthcare_map.html")
    print("Map saved.")
