import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load MapPLUTO (only residential parcels in Manhattan)
print("Loading MapPLUTO...")
gdf = gpd.read_file("data/MapPLUTO25v4.gdb", layer="MapPLUTO_25v4_clipped")

# Filter to Manhattan and residential zones only
gdf = gdf[gdf["Borough"] == "MN"]
gdf = gdf[gdf["ZoneDist1"].str.startswith("R", na=False)]

print(f"Loaded {len(gdf)} residential parcels in Manhattan")
print(gdf[["BBL", "ZoneDist1", "UnitsRes", "LotArea"]].head())

# Load subway stations
print("Loading subway stations...")
stations_df = pd.read_csv("data/Stations.csv")

# Create geometry from lat/long columns
stations_gdf = gpd.GeoDataFrame(
    stations_df,
    geometry=gpd.points_from_xy(stations_df["GTFS Longitude"], stations_df["GTFS Latitude"]),
    crs="EPSG:4326"
)

print(f"Loaded {len(stations_gdf)} subway stations")
print(stations_gdf[["Stop Name", "Borough", "geometry"]].head())