import requests


# ---------------------------------------------------------
# OLLAMA CONFIGURATION
# ---------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


# ---------------------------------------------------------
# SEND PROMPT TO OLLAMA
# ---------------------------------------------------------

def ask_llm(prompt: str) -> str:

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
        raise RuntimeError(
            f"Ollama response did not contain response: {data}"
        )

    return data["response"]


# ---------------------------------------------------------
# EXTRACT FACTUAL CLAIMS
# ---------------------------------------------------------

def extract_claims(news_text: str) -> str:

    prompt = f"""
You are an expert fact-checking assistant.

Read the following news article and extract ONLY the most important
factual claims that should be fact-checked.

ARTICLE:
{news_text}


RULES:

1. Extract a maximum of 3 claims.

2. Extract only claims that are central to the article.

3. Each claim must be a specific factual statement.

4. Each claim must be independently verifiable using external sources.

5. Use ONLY facts explicitly stated in the article.

6. Do NOT add information from your own knowledge.

7. Do NOT include opinions.

8. Do NOT include interpretations.

9. Do NOT include generalizations.

10. Do NOT include vague statements.

11. Do NOT repeat the same event in different wording.

12. Prefer claims involving:
    - a specific person
    - a specific organization
    - a specific action
    - a specific date
    - a specific number
    - a specific event
    - a specific announcement
    - a specific policy or rule

13. Preserve important dates and numbers exactly as they
    appear in the article.

14. Do not add social-media usernames unless they are essential
    to the factual claim.

15. If only 1 or 2 strong claims exist, return only those claims.

16. Do NOT force the output to contain 3 claims.

17. Every claim must describe an actual event, action,
    statement, number, date, organization, person, policy,
    rule, or factual occurrence reported in the article.

18. NEVER create a claim about what the article does or does
    not mention.

19. NEVER create claims about missing information.

20. The following are INVALID claims and MUST NOT be returned:

    - "The article does not mention..."
    - "The article doesn't mention..."
    - "The article does not specify..."
    - "The article doesn't specify..."
    - "The article does not state..."
    - "The article fails to state..."
    - "The article fails to mention..."
    - "No date is given..."
    - "No date was given..."
    - "No person is mentioned..."
    - "No person was mentioned..."
    - "The exact details are not specified..."
    - "The exact details are not mentioned..."
    - "The details are not specified..."
    - "The details are not provided..."

21. Do NOT turn missing information into a claim.

22. A claim must describe something that actually happened
    or was actually stated in the article.

23. If there are only 2 valid factual claims, return exactly
    2 claims.

24. If there is only 1 valid factual claim, return exactly
    1 claim.

25. Do not invent a third claim.

26. Return ONLY the claims.
31. Do NOT extract trivial or self-evident claims.
32. Do NOT extract claims that merely restate the article title.
33. Do NOT extract claims about the current year or event year unless
    the year itself is disputed or materially important.
34. Do NOT extract claims that only identify the year, location, or
    general existence of an event.
35. Do NOT extract claims that add no meaningful fact beyond the
    wording of the headline.
36. Prefer claims involving a concrete event, result, number,
    decision, announcement, action, person, organization, or policy.

FORMAT:

CLAIM 1: <factual claim>
CLAIM 2: <factual claim>
CLAIM 3: <factual claim>

Do not return explanations.
Do not return introductions.
Do not return conclusions.
"""


    return ask_llm(prompt)


# ---------------------------------------------------------
# VERIFY A CLAIM USING EXTERNAL EVIDENCE
# ---------------------------------------------------------

def verify_claim(claim: str, evidence: str) -> str:

    prompt = f"""
You are an expert fact-checking assistant.

Your task is to evaluate the following factual claim using ONLY
the provided evidence.

CLAIM:
{claim}

EVIDENCE:
{evidence}


IMPORTANT RULES:

1. Use ONLY the provided evidence.

2. Do NOT use outside knowledge.

3. Do NOT invent facts.

4. Do NOT assume that the claim is true.

5. If the evidence clearly supports the claim, return SUPPORTED.

6. If the evidence clearly contradicts the claim, return REFUTED.

7. If the evidence is insufficient, unclear, unrelated, or missing,
   return INCONCLUSIVE.

8. Keep the explanation short.

9. The verdict must be exactly one of:
   SUPPORTED
   REFUTED
   INCONCLUSIVE


RETURN EXACTLY THIS FORMAT:

VERDICT: SUPPORTED / REFUTED / INCONCLUSIVE
EXPLANATION: <short explanation based only on the evidence>
"""

    return ask_llm(prompt)