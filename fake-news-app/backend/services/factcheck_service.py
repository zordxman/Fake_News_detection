from .llm import extract_claims, verify_claim
from .retrieval import search_evidence


def parse_claims(raw_claims):
    claims = []

    if not raw_claims:
        return claims

    blocked_patterns = [
        "the article does not",
        "the article doesn't",
        "the article fails to",
        "the article does not specify",
        "the article does not mention",
        "the article does not state",
        "the exact details",
        "exact details",
        "details are not specified",
        "details are not mentioned",
        "details are not provided",
        "no date is given",
        "no date was given",
        "no date is mentioned",
        "no date was mentioned",
        "no date is provided",
        "no date was provided",
        "no person is mentioned",
        "no person was mentioned",
        "no person is specified",
        "no person was specified",
    ]

    for line in raw_claims.splitlines():
        line = line.strip()

        if not line.upper().startswith("CLAIM"):
            continue

        if ":" not in line:
            continue

        claim = line.split(":", 1)[1].strip()

        if not claim:
            continue

        lower = claim.lower()

        if any(pattern in lower for pattern in blocked_patterns):
            continue

        if "article" in lower and any(
            phrase in lower
            for phrase in [
                "does not",
                "doesn't",
                "not specified",
                "not mentioned",
                "not provided",
                "fails to",
            ]
        ):
            continue

        # Avoid inferred intentions/benefits.
        if any(
            phrase in lower
            for phrase in [
                "is intended to",
                "is meant to",
                "aims to",
                "aimed at",
                "is designed to",
                "will benefit",
                "will help",
                "is expected to",
                "the move will",
                "the move is to",
                "the policy will help",
            ]
        ):
            continue

        if claim not in claims:
            claims.append(claim)

    return claims[:3]


def parse_verdict(verification):
    if not verification:
        return "INCONCLUSIVE"

    text = verification.upper().strip()

    if "VERDICT:" in text:
        part = text.split("VERDICT:", 1)[1].strip()
        if part:
            word = part.split()[0]
            if word in {"SUPPORTED", "REFUTED", "INCONCLUSIVE"}:
                return word

    if "REFUTED" in text:
        return "REFUTED"

    if "SUPPORTED" in text:
        return "SUPPORTED"

    return "INCONCLUSIVE"


def fact_check_news(news_text: str):
    if not news_text or not news_text.strip():
        raise ValueError("News text cannot be empty.")

    raw_claims = extract_claims(news_text)
    claims = parse_claims(raw_claims)

    if not claims:
        return {
            "claims": [],
            "final_verdict": "INCONCLUSIVE",
            "message": "No valid factual claims were extracted.",
        }

    results = []

    for claim in claims:
        try:
            evidence = search_evidence(claim, max_records=5)
        except Exception as exc:
            evidence = []
            search_error = str(exc)
        else:
            search_error = ""

        if not evidence:
            results.append({
                "claim": claim,
                "verdict": "INCONCLUSIVE",
                "evidence": [],
                "verification": (
                    "VERDICT: INCONCLUSIVE\n"
                    "EXPLANATION: No external evidence was retrieved."
                    + (
                        f" Search error: {search_error}"
                        if search_error else ""
                    )
                ),
            })
            continue

        evidence_text = ""

        for i, item in enumerate(evidence, 1):
            evidence_text += (
                f"Evidence {i}\n"
                f"Title: {item.get('title', '')}\n"
                f"Source type: {item.get('source_type', '')}\n"
                f"Publisher: {item.get('publisher', '')}\n"
                f"URL: {item.get('publisher_url', '')}\n"
                f"Published: {item.get('published', '')}\n"
                f"Content: {item.get('text', '')[:4000]}\n\n"
            )

        try:
            verification = verify_claim(
                claim,
                evidence_text,
            )
        except Exception as exc:
            verification = (
                "VERDICT: INCONCLUSIVE\n"
                f"EXPLANATION: Verification unavailable: {exc}"
            )

        results.append({
            "claim": claim,
            "verdict": parse_verdict(verification),
            "evidence": evidence,
            "verification": verification,
        })

    verdicts = [r["verdict"] for r in results]

    if "REFUTED" in verdicts:
        final_verdict = "REFUTED"
    elif verdicts and all(v == "SUPPORTED" for v in verdicts):
        final_verdict = "SUPPORTED"
    else:
        final_verdict = "INCONCLUSIVE"

    return {
        "claims": results,
        "final_verdict": final_verdict,
        "message": (
            "Final verdict is based on external evidence and claim "
            "verification. Authoritative sources are prioritized."
        ),
    }
