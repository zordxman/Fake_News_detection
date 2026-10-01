from .llm import extract_claims, verify_claim
from .retrieval import search_evidence


# =========================================================
# PARSE CLAIMS
# =========================================================

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
        "details were not specified",
        "details were not mentioned",
        "details were not provided",
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
        "does not mention",
        "does not specify",
        "does not state",
        "doesn't mention",
        "doesn't specify",
        "doesn't state",
        "fails to mention",
        "fails to specify",
        "fails to state",
        "not specified in the article",
        "not mentioned in the article",
        "not provided in the article",
    ]

    for line in raw_claims.splitlines():

        line = line.strip()

        # Only process CLAIM lines
        if not line.upper().startswith("CLAIM"):
            continue

        # Must contain :
        if ":" not in line:
            continue

        claim = line.split(":", 1)[1].strip()

        if not claim:
            continue

        claim_lower = claim.lower()

        # -------------------------------------------------
        # Reject claims about missing information
        # -------------------------------------------------

        if (
            "article" in claim_lower
            and any(
                phrase in claim_lower
                for phrase in [
                    "does not",
                    "doesn't",
                    "not specified",
                    "not mentioned",
                    "not provided",
                    "fails to"
                ]
            )
        ):
            continue

        if any(
            phrase in claim_lower
            for phrase in [
                "details are not",
                "details were not",
                "exact details",
                "no date",
                "no person"
            ]
        ):
            continue

        if any(
            pattern in claim_lower
            for pattern in blocked_patterns
        ):
            continue

        # -------------------------------------------------
        # Reject trivial claims
        # -------------------------------------------------

        trivial_claims = [
            "the year",
            "current year",
            "the event is taking place",
            "the event takes place",
            "the games are taking place",
            "the article is about",
        ]

        if any(
            phrase in claim_lower
            for phrase in trivial_claims
        ):
            continue

        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        if claim not in claims:
            claims.append(claim)

    # Maximum 3 claims
    return claims[:3]


# =========================================================
# PARSE VERDICT
# =========================================================

def parse_verdict(verification):

    if not verification:
        return "INCONCLUSIVE"

    text = verification.upper().strip()

    # Expected format:
    #
    # VERDICT: SUPPORTED
    # EXPLANATION: ...
    #

    if "VERDICT:" in text:

        verdict_part = text.split(
            "VERDICT:",
            1
        )[1].strip()

        if verdict_part:

            first_word = verdict_part.split()[0]

            if first_word in [
                "SUPPORTED",
                "REFUTED",
                "INCONCLUSIVE"
            ]:
                return first_word

    # Fallback
    if "REFUTED" in text:
        return "REFUTED"

    if "SUPPORTED" in text:
        return "SUPPORTED"

    return "INCONCLUSIVE"


# =========================================================
# MAIN FACT CHECK FUNCTION
# =========================================================

def fact_check_news(news_text: str):

    if not news_text or not news_text.strip():

        raise ValueError(
            "News text cannot be empty."
        )

    print("\n" + "=" * 80)
    print("FACT CHECK START")
    print("=" * 80)

    # =====================================================
    # STEP 1: EXTRACT CLAIMS
    # =====================================================

    print("\n[1] Extracting claims...")

    try:

        raw_claims = extract_claims(
            news_text
        )

    except Exception as exc:

        print(
            "Claim extraction failed:",
            exc
        )

        return {
            "claims": [],
            "final_verdict": "INCONCLUSIVE",
            "message": (
                "Claim extraction failed."
            )
        }

    print("\nRaw claims:")
    print(raw_claims)

    claims = parse_claims(
        raw_claims
    )

    print("\nParsed claims:")

    for index, claim in enumerate(
        claims,
        start=1
    ):
        print(
            f"{index}. {claim}"
        )

    # =====================================================
    # NO VALID CLAIMS
    # =====================================================

    if not claims:

        print(
            "\nNo valid factual claims found."
        )

        return {
            "claims": [],
            "final_verdict": "INCONCLUSIVE",
            "message": (
                "No valid factual claims were extracted "
                "from the article."
            )
        }

    # =====================================================
    # STEP 2: VERIFY EACH CLAIM
    # =====================================================

    results = []

    for claim_index, claim in enumerate(
        claims,
        start=1
    ):

        print("\n" + "=" * 80)
        print(
            f"CLAIM {claim_index}"
        )
        print("=" * 80)

        print(
            "\nClaim:",
            claim
        )

        # -------------------------------------------------
        # Retrieve external evidence
        # -------------------------------------------------

        print(
            "\nSearching external evidence..."
        )

        try:

            evidence = search_evidence(
                claim,
                max_records=5
            )

        except Exception as exc:

            print(
                "Evidence retrieval failed:",
                exc
            )

            evidence = []

        print(
            "Evidence returned:",
            len(evidence)
        )

        # -------------------------------------------------
        # Build evidence text for Ollama
        # -------------------------------------------------

        evidence_text = ""

        for i, item in enumerate(
            evidence,
            start=1
        ):

            title = item.get(
                "title",
                ""
            )

            publisher = item.get(
                "source",
                ""
            )

            url = item.get(
                "url",
                ""
            )

            published = item.get(
                "date",
                ""
            )

            article_text = (
                item.get(
                    "article_text",
                    ""
                )
                or item.get(
                    "snippet",
                    ""
                )
                or item.get(
                    "evidence_text",
                    ""
                )
            )

            evidence_text += (
                f"Evidence {i}\n"
                f"Title: {title}\n"
                f"Publisher: {publisher}\n"
                f"URL: {url}\n"
                f"Published: {published}\n"
                f"Content:\n"
                f"{article_text[:4000]}\n\n"
            )

        # -------------------------------------------------
        # If no evidence was found
        # -------------------------------------------------

        if not evidence_text.strip():

            print(
                "No usable evidence found."
            )

            verification = (
                "VERDICT: INCONCLUSIVE\n"
                "EXPLANATION: "
                "No usable external evidence was retrieved."
            )

        else:

            print(
                f"Sending{len(evidence)} evidence to Ollama..."
            )

            try:

                verification = verify_claim(
                    claim,
                    evidence_text
                )

            except Exception as exc:

                print(
                    "Ollama verification failed:",
                    exc
                )

                verification = (
                    "VERDICT: INCONCLUSIVE\n"
                    f"EXPLANATION: "
                    f"Verification unavailable: {str(exc)}"
                )

        # -------------------------------------------------
        # Parse verdict
        # -------------------------------------------------

        verdict = parse_verdict(
            verification
        )

        print(
            "\nOllama verification:"
        )

        print(
            verification
        )

        print(
            "\nParsed verdict:",
            verdict
        )

        # -------------------------------------------------
        # Save result
        # -------------------------------------------------

        results.append({

            "claim": claim,

            "verdict": verdict,

            "evidence": evidence,

            "verification": verification

        })

    # =====================================================
    # STEP 3: FINAL VERDICT
    # =====================================================

    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    verdicts = [
        result["verdict"]
        for result in results
    ]

    # -----------------------------------------------------
    # If any claim is REFUTED
    # -----------------------------------------------------

    if "REFUTED" in verdicts:

        final_verdict = "REFUTED"

    # -----------------------------------------------------
    # If every claim is SUPPORTED
    # -----------------------------------------------------

    elif (
        verdicts
        and all(
            verdict == "SUPPORTED"
            for verdict in verdicts
        )
    ):

        final_verdict = "SUPPORTED"

    # -----------------------------------------------------
    # Otherwise
    # -----------------------------------------------------

    else:

        final_verdict = "INCONCLUSIVE"

    print(
        "Final verdict:",
        final_verdict
    )

    print(
        "All claim verdicts:",
        verdicts
    )

    # =====================================================
    # RETURN API RESPONSE
    # =====================================================

    return {

        "claims": results,

        "final_verdict": final_verdict,

        "message": (
            "Final verdict is based on retrieved "
            "external evidence and claim verification."
        )

    }