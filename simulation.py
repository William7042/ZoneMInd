import os
import datetime
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from zoning_rules import ZONING_RULES, get_far

# Zip code to neighborhood mapping for Manhattan
ZIP_TO_NEIGHBORHOOD = {
    "10001": "Chelsea/Hudson Yards",
    "10002": "Lower East Side",
    "10003": "East Village",
    "10004": "Financial District",
    "10005": "Financial District",
    "10006": "Financial District",
    "10007": "Tribeca",
    "10009": "East Village",
    "10010": "Gramercy",
    "10011": "Chelsea",
    "10012": "SoHo/NoHo",
    "10013": "SoHo/Tribeca",
    "10014": "West Village",
    "10016": "Murray Hill",
    "10017": "Midtown East",
    "10018": "Midtown",
    "10019": "Midtown West",
    "10020": "Midtown",
    "10021": "Upper East Side",
    "10022": "Midtown East",
    "10023": "Upper West Side",
    "10024": "Upper West Side",
    "10025": "Upper West Side",
    "10026": "Harlem",
    "10027": "Harlem",
    "10028": "Upper East Side",
    "10029": "East Harlem",
    "10030": "Harlem",
    "10031": "Hamilton Heights",
    "10032": "Washington Heights",
    "10033": "Washington Heights",
    "10034": "Inwood",
    "10035": "East Harlem",
    "10036": "Midtown",
    "10037": "Harlem",
    "10038": "Financial District",
    "10039": "Harlem",
    "10040": "Inwood",
}

#populated once on first call to run_simulation()
_gdf = None
_stations_gdf = None


def _load_data():
    """Load and preprocess parcel + station data. Runs once; reuses cache after."""
    global _gdf, _stations_gdf
    if _gdf is not None:
        return  # Already loaded

    cache_path = "output/manhattan_residential.geojson"

    if os.path.exists(cache_path):
        print("Loading from cache...")
        gdf = gpd.read_file(cache_path)
    else:
        print("Loading MapPLUTO")
        gdf = gpd.read_file("data/MapPLUTO25v4.gdb", layer="MapPLUTO_25v4_clipped")
        gdf = gdf[gdf["Borough"] == "MN"]
        gdf = gdf[gdf["ZoneDist1"].str.startswith("R", na=False)]
        gdf.to_crs("EPSG:4326").to_file(cache_path, driver="GeoJSON")
        print(f"Saved cache to {cache_path}")

    print(f"Loaded {len(gdf)} residential parcels in Manhattan")

    # ==============================================================================
    # STEP 2: Load subway stations and convert lat/long to point geometries
    # ==============================================================================
    print("Loading subway stations...")
    stations_df = pd.read_csv("data/Stations.csv")

    stations_gdf = gpd.GeoDataFrame(
        stations_df,
        geometry=gpd.points_from_xy(stations_df["GTFS Longitude"], stations_df["GTFS Latitude"]),
        crs="EPSG:4326"
    )
    print(f"Loaded {len(stations_gdf)} subway stations")

    # ==============================================================================
    # STEP 3: Reproject and flag parcels near subway (default 0.5 mile buffer)
    # ==============================================================================
    gdf = gdf.to_crs("EPSG:3857")
    stations_gdf = stations_gdf.to_crs("EPSG:3857")

    print("Buffering subway stations...")
    stations_gdf["geometry"] = stations_gdf.buffer(804)

    gdf = gpd.sjoin(gdf, stations_gdf[["geometry"]], how="left", predicate="intersects")
    gdf["near_subway"] = ~gdf["index_right"].isna()
    gdf = gdf.drop(columns=["index_right"]).drop_duplicates(subset=["BBL"])

    print(f"Parcels near subway: {gdf['near_subway'].sum()}")
    print(f"Parcels not near subway: {(~gdf['near_subway']).sum()}")

    _gdf = gdf
    _stations_gdf = stations_gdf


# ==============================================================================
# STEP 4: run_simulation() — called from the UI on every policy run
# ==============================================================================

def run_simulation(from_zones, to_zone, buffer_meters=804):
    """
    Simulates upzoning parcels from one or more zones to a target zone.

    from_zones: list of zones to upzone e.g. ["R6", "R6A", "R6B"]
    to_zone: zone to upzone to e.g. "R8"
    buffer_meters: distance from subway to apply upzoning (default 804m = 0.5 miles)
    Returns a dict with simulation summary + saves parcels.geojson
    """
    _load_data()  # no-op if already loaded

    # Work on a copy so original data is never modified
    sim = _gdf.copy()

    # Rebuild subway buffer with the specified distance
    stations_buffered = _stations_gdf.copy()
    stations_buffered["geometry"] = _stations_gdf.buffer(buffer_meters)
    sim = gpd.sjoin(sim, stations_buffered[["geometry"]], how="left", predicate="intersects")
    sim["near_subway"] = ~sim["index_right"].isna()
    sim = sim.drop(columns=["index_right"]).drop_duplicates(subset=["BBL"])

    # Get FAR values for before and after
    to_far = ZONING_RULES.get(to_zone, {}).get("max_far", 0)

    sim["far_before"] = sim["ZoneDist1"].apply(lambda z: get_far(z) or 0 if isinstance(z, str) else 0)

    zone_match = sim["ZoneDist1"].apply(
        lambda z: any(z.startswith(fz) for fz in from_zones) if isinstance(z, str) else False
    )
    affected = zone_match & sim["near_subway"]

    sim["far_after"] = sim.apply(
        lambda row: to_far if affected[row.name] else row["far_before"], axis=1
    )

    # Estimate units: 1 unit per 1000 sq ft of floor area
    sim["units_before"] = (sim["LotArea"] * sim["far_before"] / 1000).round()
    sim["units_after"] = (sim["LotArea"] * sim["far_after"] / 1000).round()
    sim["units_gained"] = (sim["units_after"] - sim["units_before"]).clip(lower=0)

    # ==========================================================================
    # Displacement risk score per parcel (0-10 scale)
    # Formula: underdevelopment + speculation + building age + units + small building
    # ==========================================================================

    # 1. Underdevelopment score — how much of allowed FAR is unused
    sim["far_utilized"] = (sim["BldgArea"] / (sim["LotArea"] * sim["far_before"])).clip(0, 1).fillna(0)
    underdevelopment_score = 1 - sim["far_utilized"]

    # 2. Speculation score — land value as share of total assessed value
    sim["AssessBldg"] = (sim["AssessTot"] - sim["AssessLand"]).clip(lower=1)
    speculation_score_normalized = (sim["AssessLand"] / sim["AssessTot"]).clip(0, 1).fillna(0)

    # 3. Building age score — older buildings have more rent stabilized tenants
    median_year = sim[sim["YearBuilt"] > 0]["YearBuilt"].median()
    sim["YearBuilt"] = sim["YearBuilt"].replace(0, median_year)
    current_year = datetime.datetime.now().year
    building_age_score = ((current_year - sim["YearBuilt"]) / 100).clip(0, 1).fillna(0)

    # 4. Units at risk score — capped at 50 units
    units_at_risk_score = (sim["UnitsRes"] / 50).clip(0, 1).fillna(0)

    # 5. Small building score — under 10 units = more likely rent stabilized
    small_building_score = (sim["UnitsRes"] < 10).astype(float)

    # Weighted formula
    sim["parcel_risk"] = (
        underdevelopment_score * 0.30 +
        speculation_score_normalized * 0.20 +
        building_age_score * 0.20 +
        units_at_risk_score * 0.15 +
        small_building_score * 0.15
    ) * 10

    # Only assign risk to affected parcels, zero out everyone else
    sim["parcel_risk"] = sim["parcel_risk"].where(affected, 0).round(2)

    # Overall displacement risk = average across affected parcels
    affected_parcels = sim[affected]
    displacement_risk = round(float(affected_parcels["parcel_risk"].mean()), 2) if len(affected_parcels) > 0 else 0.0

    # Reproject back to standard lat/long for the map
    sim = sim.to_crs("EPSG:4326")

    # Save GeoJSON for the frontend
    output = sim[["BBL", "ZoneDist1", "LotArea", "UnitsRes",
                  "near_subway", "far_before", "far_after",
                  "units_before", "units_after", "units_gained",
                  "parcel_risk", "geometry"]]

    geojson_path = "output/parcels.geojson"
    output.to_file(geojson_path, driver="GeoJSON")

    # Top neighborhoods by displacement risk
    sim["neighborhood"] = (
        sim["ZipCode"]
        .astype(str)
        .str.strip()
        .str.split(".")
        .str[0]  # handles floats like "10001.0" → "10001"
        .map(ZIP_TO_NEIGHBORHOOD)
        .fillna("Other")
    )
    top_hoods = (
        sim[affected]
        .groupby("neighborhood")["parcel_risk"]
        .mean()
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )

    return {
        "parcels_affected": int(affected.sum()),
        "new_units": int(sim["units_gained"].sum()),
        "top_neighborhoods": top_hoods,
        "displacement_risk": displacement_risk,
        "geojson_path": geojson_path
    }


# ------------------------------------------------------------------------------
# Test the simulation and output GeoJSON for the frontend
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Running simulation...")
    result = run_simulation(["R6", "R6A", "R6B"], "R8", buffer_meters=804)
    print(result)
