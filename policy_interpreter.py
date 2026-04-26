import anthropic
import json
from dotenv import load_dotenv
import os
from zoning_rules import ZONING_RULES
from simulation import ZIP_TO_NEIGHBORHOOD

# Invert: lowercase neighborhood name → list of zip codes
_HOOD_TO_ZIPS = {}
for _zip, _hood in ZIP_TO_NEIGHBORHOOD.items():
    _HOOD_TO_ZIPS.setdefault(_hood.lower(), []).append(_zip)

_KNOWN_NEIGHBORHOODS = sorted(set(ZIP_TO_NEIGHBORHOOD.values()))

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Zones sorted by FAR (density) ascending
ZONES_BY_FAR = sorted(ZONING_RULES.items(), key=lambda x: x[1]["max_far"])

def _all_zones_less_dense_than(to_zone):
    to_far = ZONING_RULES.get(to_zone, {}).get("max_far", 0)
    return [z for z, rules in ZONES_BY_FAR if rules["max_far"] < to_far]

def _validate_zones(params):
    params["from_zones"] = [z for z in params.get("from_zones", []) if z in ZONING_RULES]
    if params["to_zone"] not in ZONING_RULES:
        params["to_zone"] = "R6"
    if not params["from_zones"]:
        params["from_zones"] = _all_zones_less_dense_than(params["to_zone"])
    if "buffer_meters" not in params or not isinstance(params["buffer_meters"], (int, float)):
        params["buffer_meters"] = 800
    if "near_subway_only" not in params or not isinstance(params["near_subway_only"], bool):
        params["near_subway_only"] = True
    if "summary" not in params or not params["summary"]:
        params["summary"] = "Zoning upzone proposal"

    # Resolve neighborhoods/zip codes → list of zip code strings (None = all Manhattan)
    filter_zipcodes = []
    for item in params.get("neighborhoods", []):
        item = str(item).strip()
        if item.isdigit() and len(item) == 5:
            filter_zipcodes.append(item)
        else:
            filter_zipcodes.extend(_HOOD_TO_ZIPS.get(item.lower(), []))
    params["filter_zipcodes"] = filter_zipcodes if filter_zipcodes else None

    return params

def interpret_policy(user_input):
    zone_density_ref = "\n".join(
        f"  {z}: FAR {rules['max_far']}" for z, rules in ZONES_BY_FAR
    )
    neighborhood_ref = ", ".join(_KNOWN_NEIGHBORHOODS)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""You are a zoning parser. Convert the user's policy into JSON.
Return ONLY valid JSON. No markdown, no explanation.

== ZONES FROM LEAST TO MOST DENSE ==
{zone_density_ref}

== KNOWN MANHATTAN NEIGHBORHOODS ==
{neighborhood_ref}

== OUTPUT FORMAT ==
{{
  "from_zones": [list of zone codes to upzone FROM],
  "to_zone": "zone code to upzone TO",
  "near_subway_only": <true or false>,
  "buffer_meters": <integer meters from subway, only relevant if near_subway_only is true>,
  "neighborhoods": [list of neighborhood names or 5-digit zip codes, or [] for all Manhattan],
  "summary": "one sentence plain english description"
}}

== RULES ==
1. from_zones: include EVERY zone that has a lower FAR than to_zone.
   - If the user says "all parcels" or doesn't restrict by zone type, include ALL zones less dense than to_zone.
   - Do NOT copy the example — look at the zone FAR table above and pick correctly.

2. to_zone: the target density zone. If unspecified, infer from context (e.g. "upzone" near transit usually means R7 or R8).

3. near_subway_only: set to true ONLY if the user explicitly mentions proximity to subway, transit, or a station.
   - If the user says "all parcels", "citywide", or makes no mention of subway/transit, set to false.

4. buffer_meters: only matters when near_subway_only is true. Convert to meters.
   - 1 foot = 0.3048 m → 500 ft = 152 m
   - 1 mile = 1609 m → 0.5 miles = 805 m
   - If near_subway_only is true but no distance given, use 800.

5. neighborhoods: restrict simulation to these areas only.
   - Use EXACT names from the known neighborhoods list above, or 5-digit zip codes.
   - If the user says "all of Manhattan", "citywide", or mentions no specific area, use [].
   - Match common aliases: "UES" → "Upper East Side", "UWS" → "Upper West Side", "LES" → "Lower East Side", etc.

Policy: {user_input}"""
        }]
    )

    try:
        raw = response.content[0].text.strip()
        # Strip markdown code fences if the model wraps its output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        params = json.loads(raw)
        return _validate_zones(params)
    except (json.JSONDecodeError, KeyError):
        return _validate_zones({
            "from_zones": [],
            "to_zone": "R6",
            "buffer_meters": 800,
            "summary": user_input
        })
