import streamlit as st
import pydeck as pdk
import json

st.set_page_config(page_title="ZoneMind", layout="wide")

st.title("🏙️ ZoneMind")
st.subheader("AI-Powered Zoning Policy Simulator")

st.markdown("---")

# Dummy GeoJSON parcels around Brooklyn/Queens NYC
dummy_geojson = {
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
        dummy_geojson,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="[properties.displacement_risk * 255, 100, 100, 160]",
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )
    view_state = pdk.ViewState(latitude=40.655, longitude=-73.93, zoom=12, pitch=30)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "Zone: {zone}\nNew Units: {new_units}\nDisplacement Risk: {displacement_risk}"}))

st.markdown("---")
st.header("Policy Brief")

if run_button and policy_input:
    with st.spinner("Analyzing policy..."):
        st.success("✅ Simulation complete!")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.metric("Estimated New Units", "2,340")
            st.metric("Parcels Affected", "187")
        
        with col4:
            st.metric("Avg Displacement Risk", "0.54")
            st.metric("Neighborhood Coverage", "34%")
        
        st.subheader("AI Summary")
        st.markdown(f"""
        **Proposed Policy:** {policy_input}
        
        **Analysis:** This upzoning proposal would affect approximately 187 parcels across the study area, 
        enabling an estimated 2,340 new housing units. High displacement risk is concentrated near 
        transit corridors where land values are already elevated.
        
        **Tradeoffs:** Increased density supports housing supply goals but may accelerate gentrification 
        in vulnerable neighborhoods. Consider pairing with anti-displacement protections.
        """)
elif run_button and not policy_input:
    st.warning("Please enter a policy proposal first.")
else:
    st.info("Enter a proposal and click Run Simulation to see results.")