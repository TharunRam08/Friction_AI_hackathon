# backend/modules/m4_synthesis.py
import json

def synthesize(question: str, goal: str, views: list, client) -> dict:
    views_text = json.dumps(views, indent=2)
    prompt = f"""
    You are the CEO. Your goal is: {goal}. 
    You asked: {question}.
    Your 4 department heads gave these exact independent opinions:
    {views_text}

    Reconcile these conflicting views. Identify the single biggest constraint (the binding factor).
    Produce a final, actionable, conditional recommendation (e.g., "Delay expansion, fix logistics first, then proceed").
    Also, classify the overall decision stance of this final recommendation as: "Support", "Against", or "Neutral".

    Return ONLY a valid JSON object with these exact keys: "recommendation" and "stance".
    """
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    clean_json = chat_completion.choices[0].message.content.strip()
    return json.loads(clean_json)
