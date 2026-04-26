import anthropic
import json
from dotenv import load_dotenv
import os
from zoning_rules import ZONING_RULES

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
    if "summary" not in params or not params["summary"]:
        params["summary"] = "Zoning upzone proposal"
    return params

def interpret_policy(user_input):
    zone_density_ref = "\n".join(
        f"  {z}: FAR {rules['max_far']}" for z, rules in ZONES_BY_FAR
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""You are a zoning parser. Convert the user's policy into JSON.
Return ONLY valid JSON. No markdown, no explanation.

== ZONES FROM LEAST TO MOST DENSE ==
{zone_density_ref}

== OUTPUT FORMAT ==
{{
  "from_zones": [list of zone codes to upzone FROM],
  "to_zone": "zone code to upzone TO",
  "buffer_meters": <integer meters from subway>,
  "summary": "one sentence plain english description"
}}

== RULES ==
1. from_zones: include EVERY zone that has a lower FAR than to_zone.
   - If the user says "all parcels" or doesn't restrict by zone type, include ALL zones less dense than to_zone.
   - Do NOT copy the example — look at the zone FAR table above and pick correctly.

2. to_zone: the target density zone. If unspecified, infer from context (e.g. "upzone" near transit usually means R7 or R8).

3. buffer_meters: convert to meters.
   - 1 foot = 0.3048 m → 500 ft = 152 m
   - 1 mile = 1609 m → 0.5 miles = 805 m
   - If no distance given, use 800.

Policy: {user_input}"""
        }]
    )

    try:
        params = json.loads(response.content[0].text)
        return _validate_zones(params)
    except (json.JSONDecodeError, KeyError):
        return _validate_zones({
            "from_zones": [],
            "to_zone": "R6",
            "buffer_meters": 800,
            "summary": user_input
        })
