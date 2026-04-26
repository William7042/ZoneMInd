import streamlit as st
import pydeck as pdk
import json
import os
from brief_generator import generate_brief
from policy_interpreter import interpret_policy

st.set_page_config(page_title="ZoneMind", layout="wide")

st.title("🏙️ ZoneMind")
st.subheader("AI-Powered Zoning Policy Simulator")

st.markdown("---")

# Load real GeoJSON if available, otherwise use dummy data
geojson_path = "output/parcels.geojson"

if os.path.exists(geojson_path):
    with open(geojson_path, "r") as f:
        map_data = json.load(f)
    st.sidebar.success("✅ Using real parcel data")
else:
    map_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone": "R2", "new_units": 0, "displacement_risk": 0.2},
                "geometry": {"type": "Polygon", "coordinates": [[
                    [-73.95, 40.65], [-73.94, 40.65], [-73.94, 40.66], [-73.95, 40.66], [-73.95, 40.65]
                ]]}
            },
            {
                "type": "Feature",
                "properties": {"zone": "R6", "new_units": 120, "displacement_risk": 0.7},
                "geometry": {"type": "Polygon", "coordinates": [[
                    [-73.93, 40.65], [-73.92, 40.65], [-73.92, 40.66], [-73.93, 40.66], [-73.93, 40.65]
                ]]}
            },
            {
                "type": "Feature",
                "properties": {"zone": "R4", "new_units": 45, "displacement_risk": 0.4},
                "geometry": {"type": "Polygon", "coordinates": [[
                    [-73.91, 40.65], [-73.90, 40.65], [-73.90, 40.66], [-73.91, 40.66], [-73.91, 40.65]
                ]]}
            },
        ]
    }
    st.sidebar.warning("⚠️ Using dummy data — parcels.geojson not found")

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
        get_fill_color="[properties.displacement_risk * 255, 100, 100, 160]",
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )
    view_state = pdk.ViewState(latitude=40.655, longitude=-73.93, zoom=12, pitch=30)
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Zone: {zone}\nNew Units: {new_units}\nDisplacement Risk: {displacement_risk}"}
    ))

st.markdown("---")
st.header("Policy Brief")

if run_button and policy_input:
    with st.spinner("Interpreting policy..."):
        policy_params = interpret_policy(policy_input)

    st.success("✅ Policy interpreted!")
    st.json(policy_params)

    # Dummy sim results until Person A is done
    sim_results = {
        "parcels_affected": int(sum(1 for f in map_data["features"] if (f["properties"].get("units_gained") or 0) > 0)),
        "new_units": int(sum((f["properties"].get("units_gained") or 0) for f in map_data["features"])),
        "top_neighborhoods": ["Upper West Side", "Harlem", "Midtown"],
        "displacement_risk": 5.4
    }
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Estimated New Units", f"{sim_results['new_units']:,}")
        st.metric("Parcels Affected", f"{sim_results['parcels_affected']:,}")
    with col4:
        st.metric("Avg Displacement Risk", f"{sim_results['displacement_risk']}/10")
        st.metric("Top Area", sim_results['top_neighborhoods'][0])

    st.subheader("AI Policy Brief")
    brief_placeholder = st.empty()
    full_brief = ""
    for chunk, in generate_brief(policy_params["summary"], sim_results):
        full_brief += chunk
        brief_placeholder.markdown(full_brief)

elif run_button and not policy_input:
    st.warning("Please enter a policy proposal first.")
else:
    st.info("Enter a proposal and click Run Simulation to see results.")