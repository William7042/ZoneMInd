# ZoneMind

An AI-powered NYC zoning policy simulation tool. Type a natural language upzoning proposal, and ZoneMind interprets it, runs a geospatial simulation on real parcel data, and generates a policy brief with displacement risk analysis.

---

## What It Does

1. Interprets your policy proposal using Claude Haiku (e.g. "Upzone R2 parcels within half a mile of subway stations to R6")
2. Simulates the upzoning across ~70k Manhattan residential parcels using real MapPLUTO data
3. Scores each affected parcel for displacement risk on a 0–10 scale
4. Visualizes results on an interactive map with a parcel risk gradient
5. Generates a 3-paragraph policy brief using Claude Sonnet with the actual simulation numbers

---

## Stack

- **Frontend** — Streamlit
- **Map** — PyDeck (deck.gl)
- **Geospatial** — GeoPandas, Shapely
- **Data** — NYC MapPLUTO 25v4, MTA Stations CSV
- **AI** — Anthropic Claude (Haiku for parsing, Sonnet for briefs)

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

### 3. Add data files

Place the following in the `data/` directory:

- `MapPLUTO25v4.gdb` — [Download from NYC DCP](https://www.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page)
- `Stations.csv` — MTA subway stations with `Stop Name`, `GTFS Latitude`, `GTFS Longitude` columns

### 4. Run

```bash
streamlit run app.py
```

---

## Project Structure

```
ZoneMind/
├── app.py                  # Streamlit UI + layout
├── simulation.py           # Geospatial simulation engine
├── policy_interpreter.py   # Claude Haiku — parses plain English to JSON params
├── brief_generator.py      # Claude Sonnet — streams the policy brief
├── zoning_rules.py         # NYC zoning FAR lookup table
├── data/
│   ├── MapPLUTO25v4.gdb    # NYC parcel database (not included)
│   └── Stations.csv        # MTA subway stations
└── output/
    ├── manhattan_residential.geojson   # Cached parcel data (generated on first run)
    └── parcels.geojson                 # Simulation output (generated per run)
```

---

## How the Simulation Works

### Unit Estimation
New housing capacity is estimated using NYC's Floor Area Ratio (FAR) system:

```
units = (lot_area × FAR) / 1,000
```

Units gained = `units_after - units_before`, clipped at 0.

### Displacement Risk Score (0–10)
Each affected parcel is scored on 5 factors:

| Factor | Weight | Rationale |
|---|---|---|
| Underdevelopment | 30% | Low FAR utilization → likely redevelopment target |
| Speculation | 20% | High land-to-total value ratio → speculative pressure |
| Building age | 20% | Older buildings → more rent-stabilized tenants |
| Units at risk | 15% | More existing units → more people exposed |
| Small building | 15% | Under 10 units → likely rent-stabilized under NYC law |

The score shown in the UI is the **average across all affected parcels**.

---

## Example Prompts

- `"Upzone all R2 parcels within half a mile of subway stations to R6"`
- `"Allow R6A density on all low-density residential in Harlem"`
- `"Upzone everything less dense than R7 citywide to R7A"`
- `"Rezone R4 and R5 parcels in Washington Heights to R7 near transit"`

---

## Multi-Scenario Comparison

Run multiple simulations in one session — ZoneMind stores each run and lets you toggle between Scenario 1, Scenario 2, etc. to compare maps and metrics side by side.
