import streamlit as st

st.set_page_config(page_title="ZoneMind", layout="wide")

st.title("🏙️ ZoneMind")
st.subheader("AI-Powered Zoning Policy Simulator")

st.markdown("---")

# Left column: user input | Right column: map
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
    st.info("Map will appear here once Person A's GeoJSON is ready.")

st.markdown("---")
st.header("Policy Brief")
st.info("AI-generated policy brief will appear here.")