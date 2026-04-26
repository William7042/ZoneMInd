import anthropic
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_brief(policy_summary, sim_results):
    prompt = f"""You are a senior NYC urban planning policy analyst.
Write a sharp, specific 3-paragraph policy brief based on these simulation results.
Use the exact numbers. Be honest about tradeoffs. Don't be generic.

Policy: {policy_summary}

Results:
- Parcels affected: {sim_results['parcels_affected']:,}
- Estimated new units unlocked: {sim_results['new_units']:,}
- Top neighborhoods affected: {', '.join(sim_results['top_neighborhoods'])}
- Average displacement risk score: {sim_results['displacement_risk']}/10

Paragraph 1: What the policy does and the opportunity (new units, which areas)
Paragraph 2: The displacement risk and who is most vulnerable
Paragraph 3: Recommendation — is this a good tradeoff and what safeguards are needed"""

    with client.messages.stream(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text