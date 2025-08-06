import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client=OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def analyze_code_with_gpt(code_snippet, filename):
    prompt = f"""
    Du är en erfaren Python-kodgranskare. Analysera följande fil: {filename}.
    Ge feedback om:
    - Kodstil
    - Komplexitet
    - Eventuella säkerhetsrisker
    - Möjlig refaktorering

    Kod:
    {code_snippet}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
