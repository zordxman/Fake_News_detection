import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
def ask_llm(prompt):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }    
    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()
    if "response" not in data:
        raise RuntimeError(f"Ollama response did not contain response: {data}")
    return data["response"]
def extract_claims(news_text):

    prompt = f"""
You are an expert fact-checking assistant.

Read the following news article and extract ONLY the most important
claims that should be fact-checked.

ARTICLE:
{news_text}

Rules:

1. Extract a maximum of 3 claims.
2. Extract only claims that are central to the article.
3. Each claim must be a specific factual statement.
4. Each claim must be independently verifiable using external sources.
5. Use ONLY facts explicitly stated in the article.
6. Do NOT add information from your own knowledge.
7. Do NOT include opinions.
8. Do NOT include interpretations or generalizations.
9. Do NOT include phrases such as:
   - "recurring phenomenon"
   - "widely believed"
   - "controversial"
   - "important"
   - "significant"
   unless they are themselves the specific factual subject being verified.
10. Do NOT include general background facts unless they are essential
    to the main story.
11. Do NOT repeat the same event in different wording.
12. Prefer claims involving:
    - a specific person
    - a specific action
    - a specific date
    - a specific statement
    - a specific event
13. Preserve important dates.
14. Do not add social-media usernames unless essential.
15. If only 1 or 2 strong claims exist, return only those claims.
16. Do NOT force the output to contain 3 claims.

Return ONLY:

CLAIM 1: <factual claim>
CLAIM 2: <factual claim>
CLAIM 3: <factual claim>
"""

    return ask_llm(prompt)