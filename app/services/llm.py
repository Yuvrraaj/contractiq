from groq import Groq
from app.config import settings
import json

client = Groq(api_key=settings.groq_api_key)


async def analyse_contract(content: str) -> dict:
    """Send contract to Llama 3.3 70B via Groq and get structured analysis back."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a contract analysis assistant.
Analyse the provided contract and return a JSON object with exactly these fields:
- summary: one sentence summary
- parties: list of party names mentioned
- key_obligations: list of the 3 most important obligations
- risk_level: one of "low", "medium", "high"
- risk_reasons: list of reasons for the risk level

Return ONLY the JSON object, no other text, no markdown, no backticks.""",
            },
            {
                "role": "user",
                "content": f"<contract>\n{content}\n</contract>",
            },
        ],
        temperature=0.1,  # low temperature = more deterministic JSON output
        max_tokens=1024,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw)