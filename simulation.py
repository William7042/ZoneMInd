import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# ==============================================================================
# STEP 1: Load MapPLUTO parcel data
# Each row = one parcel of land in NYC, with shape + zoning + building info
# ==============================================================================
print("Loading MapPLUTO...")
gdf = gpd.read_file("data/MapPLUTO25v4.gdb", layer="MapPLUTO_25v4_clipped")

# Keep only Manhattan residential parcels (ZoneDist1 starting with "R")
gdf = gdf[gdf["Borough"] == "MN"]
gdf = gdf[gdf["ZoneDist1"].str.startswith("R", na=False)]

print(f"Loaded {len(gdf)} residential parcels in Manhattan")
print(gdf[["BBL", "ZoneDist1", "UnitsRes", "LotArea"]].head())

# ==============================================================================
# STEP 2: Load subway stations and convert lat/long to point geometries
# ==============================================================================
print("Loading subway stations...")
stations_df = pd.read_csv("data/Stations.csv")

# Convert lat/long columns into actual geometry points geopandas understands
stations_gdf = gpd.GeoDataFrame(
    stations_df,
    geometry=gpd.points_from_xy(stations_df["GTFS Longitude"], stations_df["GTFS Latitude"]),
    crs="EPSG:4326"  # Standard lat/long coordinate system
)

print(f"Loaded {len(stations_gdf)} subway stations")
print(stations_gdf[["Stop Name", "Borough", "geometry"]].head())

# ==============================================================================
# STEP 3: Buffer subway stations and flag nearby parcels
# ==============================================================================

# Reproject to meter-based CRS so we can buffer in meters, not degrees
gdf = gdf.to_crs("EPSG:3857")
stations_gdf = stations_gdf.to_crs("EPSG:3857")

# Draw a 0.5 mile (804 meter) circle around each station
print("Buffering subway stations...")
stations_gdf["geometry"] = stations_gdf.buffer(804)

# Spatial join: flag any parcel that intersects a station buffer circle
gdf = gpd.sjoin(gdf, stations_gdf[["geometry"]], how="left", predicate="intersects")
gdf["near_subway"] = ~gdf["index_right"].isna()  # True if parcel is near a station
gdf = gdf.drop(columns=["index_right"]).drop_duplicates(subset=["BBL"])

print(f"Parcels near subway: {gdf['near_subway'].sum()}")
print(f"Parcels not near subway: {(~gdf['near_subway']).sum()}")