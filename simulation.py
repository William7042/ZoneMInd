import geopandas as gpd

# Load MapPLUTO (only residential parcels in Manhattan)
print("Loading MapPLUTO...")
gdf = gpd.read_file("data/MapPLUTO25v4.gdb", layer="MapPLUTO_25v4_clipped")

# Filter to Manhattan and residential zones only
gdf = gdf[gdf["Borough"] == "MN"]
gdf = gdf[gdf["ZoneDist1"].str.startswith("R", na=False)]

print(f"Loaded {len(gdf)} residential parcels in Manhattan")
print(gdf[["BBL", "ZoneDist1", "UnitsRes", "LotArea"]].head())