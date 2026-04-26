import streamlit as st
import pydeck as pdk
import json
import os
import pandas as pd
from brief_generator import generate_brief
from policy_interpreter import interpret_policy

try:
    from simulation import run_simulation
    simulation_available = True
except Exception as e:
    simulation_available = False
    simulation_error = str(e)

st.set_page_config(page_title="ZoneMind", layout="wide")

st.title("🏙️ ZoneMind")
st.subheader("AI-Powered Zoning Policy Simulator")

st.markdown("---")

# Session state — persists across reruns
if "sim_results" not in st.session_state:
    st.session_state.sim_results = None
if "policy_params" not in st.session_state:
    st.session_state.policy_params = None
if "brief_text" not in st.session_state:
    st.session_state.brief_text = None

# Load GeoJSON — only show parcels after a simulation has been run this session
geojson_path = "output/parcels.geojson"

if st.session_state.sim_results and os.path.exists(geojson_path):
    with open(geojson_path, "r") as f:
        map_data = json.load(f)
else:
    map_data = {"type": "FeatureCollection", "features": []}

# Load subway stations
stations_df = pd.read_csv("data/Stations.csv")
stations_data = stations_df[["Stop Name", "GTFS Latitude", "GTFS Longitude"]].rename(
    columns={"GTFS Latitude": "lat", "GTFS Longitude": "lon"}
).to_dict("records")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Policy Input")
    policy_input = st.text_area(
        "Describe your zoning proposal:",
        placeholder="e.g. Upzone all parcels within 0.5 miles of subway stations from R2 to R6",
        height=150
    )
    run_button = st.button("Run Simulation", type="primary")

with col2:
    st.header("Map")
    layer = pdk.Layer(
        "GeoJsonLayer",
        map_data,
        pickable=True,
        stroked=True,
        filled=True,
        # parcel_risk is 0–10: low=green, high=red
        get_fill_color="[properties.parcel_risk * 25, 255 - properties.parcel_risk * 25, 50, 180]",
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )
    station_layer = pdk.Layer(
        "ScatterplotLayer",
        stations_data,
        get_position="[lon, lat]",
        radius_min_pixels=4,
        radius_max_pixels=6,
        get_fill_color=[255, 220, 0, 220],
        pickable=False,
    )
    view_state = pdk.ViewState(latitude=40.728, longitude=-73.994, zoom=11, pitch=30)
    st.pydeck_chart(pdk.Deck(
        layers=[layer, station_layer],
        initial_view_state=view_state,
        tooltip={"text": "Zone: {ZoneDist1}\nUnits Gained: {units_gained}\nDisplacement Risk: {parcel_risk}/10"}
    ))

st.markdown("---")
st.header("Simulation Results")

if run_button and not policy_input:
    st.warning("Please enter a policy proposal first.")

elif run_button and policy_input:
    if not simulation_available:
        st.error(f"Simulation unavailable — data files missing. ({simulation_error})")
    else:
        with st.spinner("Interpreting policy..."):
            policy_params = interpret_policy(policy_input)

        with st.spinner("Running simulation (this may take a moment)..."):
            sim_results = run_simulation(
                policy_params["from_zones"],
                policy_params["to_zone"],
                policy_params.get("buffer_meters", 800),
                policy_params.get("near_subway_only", True)
            )

        # Store results and trigger a clean rerun so the map reloads from the new GeoJSON
        st.session_state.sim_results = sim_results
        st.session_state.policy_params = policy_params
        st.session_state.brief_text = None
        st.rerun()

if st.session_state.sim_results:
    sim_results = st.session_state.sim_results
    policy_params = st.session_state.policy_params

    with st.expander("Interpreted policy parameters"):
        st.json(policy_params)

    col3, col4 = st.columns(2)
    with col3:
        st.metric("Estimated New Units", f"{sim_results['new_units']:,}")
        st.metric("Parcels Affected", f"{sim_results['parcels_affected']:,}")
    with col4:
        st.metric("Avg Displacement Risk", f"{sim_results['displacement_risk']}/10")
        top_area = sim_results["top_neighborhoods"][0] if sim_results["top_neighborhoods"] else "N/A"
        st.metric("Top At-Risk Area", top_area)

    st.subheader("AI Policy Brief")
    if st.session_state.brief_text:
        # Show cached brief on subsequent reruns (avoids re-generating)
        st.markdown(st.session_state.brief_text)
    else:
        brief_placeholder = st.empty()
        full_brief = ""
        for chunk in generate_brief(policy_params["summary"], sim_results):
            full_brief += chunk
            brief_placeholder.markdown(full_brief)
        st.session_state.brief_text = full_brief

else:
    st.info("Enter a proposal and click Run Simulation to see results.")
