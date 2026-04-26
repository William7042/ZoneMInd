import anthropic
import json
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def interpret_policy(user_input):
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Convert this zoning policy into structured parameters.
Return ONLY valid JSON, no explanation, no markdown.

Format:
{{
  "from_zones": ["R2", "R3", "R4"],
  "to_zone": "R6",
  "buffer_meters": 600,
  "summary": "one sentence plain english summary of the policy"
}}

Rules:
- from_zones should be all zones LESS dense than to_zone
- buffer_meters is how far from subway stations the policy applies
- if no distance mentioned, default to 800 meters
- to_zone should be the target upzone destination

Policy: {user_input}"""
        }]
    )

    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        # fallback default
        return {
            "from_zones": ["R2", "R3", "R4"],
            "to_zone": "R6",
            "buffer_meters": 800,
            "summary": user_input
        }