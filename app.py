import streamlit as st
import pydeck as pdk
import json
import pandas as pd
from brief_generator import generate_brief
from policy_interpreter import interpret_policy

try:
    from simulation import run_simulation
    simulation_available = True
except Exception as e:
    simulation_available = False
    simulation_error = str(e)

st.set_page_config(
    page_title="ZoneMind",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(99,102,241,.08), transparent 32%),
        linear-gradient(180deg,#fbfbfd 0%,#ffffff 45%,#f8fafc 100%);
    color:#0f172a;
}

.block-container {
    max-width: 1680px;
    padding-top: 4.25rem !important;
    padding-left: 2rem;
    padding-right: 2rem;
    padding-bottom: 2rem;
}

div[data-testid="stVerticalBlock"] {
    gap: 1rem;
}

/* ---------- Header ---------- */
.top-header {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 1.05rem 1.5rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(15,23,42,.04);
}

.logo-wrap {
    display: flex;
    align-items: center;
    gap: .9rem;
}

.logo-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: #eef2ff;
    color: #4f46e5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
}

.logo-text {
    font-size: 2rem;
    font-weight: 850;
    letter-spacing: -.04em;
    color: #0f172a;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    color: #111827;
    font-size: 1.15rem;
}

.menu-dots {
    font-size: 1.7rem;
    line-height: 1;
}

/* ---------- White Cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 30px rgba(15,23,42,.05) !important;
    padding: 1.15rem !important;
}

/* ---------- Text ---------- */
h1, h2, h3 {
    color: #0f172a;
    letter-spacing: -.035em;
}

h3 {
    font-size: 1.85rem !important;
    font-weight: 850 !important;
    margin-bottom: .9rem !important;
}

p, li {
    font-size: 1.2rem !important;
    line-height: 1.75 !important;
}

label {
    font-size: 1.2rem !important;
    font-weight: 650 !important;
    color: #334155 !important;
}

.stCaptionContainer {
    font-size: 1.05rem !important;
}

/* ---------- Input ---------- */
.stTextArea textarea {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    min-height: 165px !important;
    padding: 1rem !important;
    font-size: 1.25rem !important;
    line-height: 1.55 !important;
}

.stButton > button {
    width: 270px;
    height: 60px;
    border: none !important;
    border-radius: 16px !important;
    font-size: 1.25rem !important;
    font-weight: 800 !important;
    color: white !important;
    background: linear-gradient(135deg,#4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
    box-shadow: 0 10px 24px rgba(79,70,229,.28);
}

.stButton > button:hover {
    transform: translateY(-2px);
}

/* ---------- Metrics ---------- */
.metric-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1.2fr 1.2fr;
    gap: 0;
    margin-top: .85rem;
}

.metric-item {
    padding: .35rem 1.05rem;
    border-right: 1px solid #e2e8f0;
}

.metric-item:last-child {
    border-right: none;
}

.metric-label {
    font-size: 1.1rem;
    font-weight: 650;
    color: #334155;
    margin-bottom: 1.15rem;
}

.metric-value {
    font-size: 2.25rem;
    font-weight: 400;
    color: #111827;
    letter-spacing: -.03em;
    line-height: 1.25;
}

.risk-circle {
    width: 98px;
    height: 98px;
    border-radius: 50%;
    background:
        radial-gradient(circle at center, white 53%, transparent 54%),
        conic-gradient(#f59e0b var(--risk), #e5e7eb 0);
    display: flex;
    align-items: center;
    justify-content: center;
}

.risk-inner {
    text-align: center;
    font-size: 1.7rem;
    font-weight: 400;
}

.risk-inner span {
    display: block;
    font-size: .9rem;
    color: #475569;
}

/* ---------- Map ---------- */
iframe {
    border-radius: 0 !important;
}

/* ---------- Legend Separate From Map Card ---------- */
.legend {
    margin-top: .75rem;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: .9rem 1rem;
    background: #ffffff;
    font-size: 1.15rem;
    box-shadow: 0 8px 24px rgba(15,23,42,.035);
}

.legendgrad {
    margin-top: .55rem;
    height: 14px;
    border-radius: 999px;
    background: linear-gradient(90deg,#22c55e,#eab308,#ef4444);
}

/* ---------- Policy Brief ---------- */
.brief-wrapper {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(15,23,42,.05);
    padding: 1.6rem 1.8rem;
    margin-top: 1rem;
}

.brief-title {
    font-size: 1.9rem;
    font-weight: 850;
    color: #0f172a;
    margin-bottom: 1rem;
    letter-spacing: -.035em;
}

.brief-content {
    width: 100%;
    max-width: 100%;
    font-size: 1.2rem;
    line-height: 1.8;
    color: #0f172a;
}

.brief-content h1 {
    font-size: 2.5rem !important;
    line-height: 1.2 !important;
}

.brief-content h2 {
    font-size: 2rem !important;
}

.brief-content h3 {
    font-size: 1.6rem !important;
}

.brief-content p {
    max-width: 100% !important;
    font-size: 1.2rem !important;
    line-height: 1.8 !important;
}

div[data-testid="stMarkdownContainer"] {
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-header">
    <div class="logo-wrap">
        <div class="logo-icon">🏙️</div>
        <div class="logo-text">ZoneMind</div>
    </div>
    <div class="header-actions">
        <span>Deploy</span>
        <span class="menu-dots">⋮</span>
    </div>
</div>
""", unsafe_allow_html=True)

if "scenarios" not in st.session_state:
    st.session_state.scenarios = []

if "active_scenario" not in st.session_state:
    st.session_state.active_scenario = 0

stations_df = pd.read_csv("data/Stations.csv")
stations_data = stations_df[["Stop Name", "GTFS Latitude", "GTFS Longitude"]].rename(
    columns={"GTFS Latitude": "lat", "GTFS Longitude": "lon"}
).to_dict("records")

scenarios = st.session_state.scenarios

if len(scenarios) > 1:
    labels = [f"Scenario {i+1}" for i, s in enumerate(scenarios)]
    selected = st.radio(
        "Compare scenarios",
        labels,
        horizontal=True,
        index=st.session_state.active_scenario
    )
    st.session_state.active_scenario = labels.index(selected)

active_idx = st.session_state.active_scenario
active = scenarios[active_idx] if scenarios else None
map_data = active["map_data"] if active else {"type": "FeatureCollection", "features": []}

left, right = st.columns([1.05, 1.65], gap="medium")

with left:
    with st.container(border=True):
        st.subheader("Policy Input")

        policy_input = st.text_area(
            "Describe your zoning proposal",
            placeholder='"Upzone all R2 parcels within a half mile of subway stations to R6 to allow apartment buildings near transit"',
            height=165
        )

        run_button = st.button("▶ Run Simulation", type="primary")

    with st.container(border=True):
        st.subheader("Key Metrics")

        if active:
            sim_results = active["sim_results"]
            risk = sim_results["displacement_risk"]
            risk_pct = min(max(risk * 10, 0), 100)
            top_area = sim_results["top_neighborhoods"][0] if sim_results["top_neighborhoods"] else "N/A"

            st.markdown(f"""
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-label">Estimated New Units</div>
                    <div class="metric-value">{sim_results['new_units']:,}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Parcels Affected</div>
                    <div class="metric-value">{sim_results['parcels_affected']:,}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Displacement Risk</div>
                    <div class="risk-circle" style="--risk:{risk_pct}%;">
                        <div class="risk-inner">{risk}<span>/10</span></div>
                    </div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Top At-Risk Area</div>
                    <div class="metric-value">{top_area}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-label">Estimated New Units</div>
                    <div class="metric-value">—</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Parcels Affected</div>
                    <div class="metric-value">—</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Displacement Risk</div>
                    <div class="metric-value">—</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Top At-Risk Area</div>
                    <div class="metric-value">—</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

with right:
    with st.container(border=True):
        st.subheader("Interactive Parcel Map")

        layer = pdk.Layer(
            "GeoJsonLayer",
            map_data,
            pickable=True,
            stroked=True,
            filled=True,
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
            tooltip={
                "text": "Zone: {ZoneDist1}\\nUnits Gained: {units_gained}\\nDisplacement Risk: {parcel_risk}/10"
            }
        ))

    st.markdown("""
    <div class="legend">
        <b>Parcel Risk Gradient</b>
        <div class="legendgrad"></div>
        <div style="display:flex;justify-content:space-between;">
            <span>Low</span><span>High</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if run_button and not policy_input:
    st.warning("Please enter a policy proposal first.")

elif run_button and policy_input:
    if not simulation_available:
        st.error(f"Simulation unavailable — data files missing. ({simulation_error})")
    else:
        with st.spinner("Interpreting policy..."):
            policy_params = interpret_policy(policy_input)

        with st.spinner("Running citywide simulation..."):
            sim_results = run_simulation(
                policy_params["from_zones"],
                policy_params["to_zone"],
                policy_params.get("buffer_meters", 800),
                policy_params.get("near_subway_only", True),
                policy_params.get("filter_zipcodes")
            )

        geojson_path = "output/parcels.geojson"
        with open(geojson_path, "r") as f:
            new_map_data = json.load(f)

        st.session_state.scenarios.append({
            "policy_params": policy_params,
            "sim_results": sim_results,
            "brief_text": None,
            "map_data": new_map_data,
        })

        st.session_state.active_scenario = len(st.session_state.scenarios) - 1
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("Policy Brief")

    if active:
        policy_params = active["policy_params"]
        sim_results = active["sim_results"]

        if active["brief_text"]:
            st.markdown(f"""
            <div class="brief-content">
                {active["brief_text"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            brief_placeholder = st.empty()
            full_brief = ""

            for chunk in generate_brief(policy_params["summary"], sim_results):
                full_brief += chunk
                brief_placeholder.markdown(full_brief)

            st.session_state.scenarios[active_idx]["brief_text"] = full_brief
    else:
        st.markdown("Run a simulation to generate a policy brief.")

if active:
    with st.expander("Interpreted Policy Parameters"):
        st.json(active["policy_params"])