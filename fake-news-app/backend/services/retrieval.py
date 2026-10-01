import re
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
    )
}


AUTHORITATIVE_DOMAINS = [
    "pmindia.gov.in",
    "presidentofindia.gov.in",
    "sansad.in",
    "pib.gov.in",
    "isro.gov.in",
    "eci.gov.in",
    "rbi.org.in",
    "trai.gov.in",
    "supremecourtofindia.nic.in",
    "mha.gov.in",
    "mea.gov.in",
    "mohfw.gov.in",
    "education.gov.in",
    "indiacode.nic.in",
    "gov.in",
]


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _domain_from_url(url: str) -> str:
    try:
        return (
            urllib.parse.urlparse(url)
            .netloc
            .lower()
            .removeprefix("www.")
        )
    except Exception:
        return ""


def _fetch_page_text(url: str) -> str:

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return ""

        content_type = response.headers.get(
            "content-type",
            ""
        )

        if "text/html" not in content_type:
            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "form",
            "svg"
        ]):
            tag.decompose()

        parts = []

        for element in soup.find_all([
            "h1",
            "h2",
            "h3",
            "p",
            "article"
        ]):

            value = _clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if value:
                parts.append(value)

        # Remove duplicates
        unique = []
        seen = set()

        for value in parts:

            if value not in seen:

                unique.append(value)
                seen.add(value)

        return " ".join(unique)[:12000]

    except Exception as exc:

        print(
            "Page fetch failed:",
            exc
        )

        return ""


def _google_news_rss(query: str):

    encoded = urllib.parse.quote_plus(query)

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    print("\nGoogle News query:")
    print(query)

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        print(
            "Google News status:",
            response.status_code
        )

        print(
            "Google News response length:",
            len(response.content)
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

        results = []

        items = root.findall(".//item")

        print(
            "RSS items found:",
            len(items)
        )

        for item in items:

            title = item.findtext(
                "title",
                default=""
            ).strip()

            link = item.findtext(
                "link",
                default=""
            ).strip()

            pub_date = item.findtext(
                "pubDate",
                default=""
            ).strip()

            description = item.findtext(
                "description",
                default=""
            )

            # Clean HTML from Google News description
            description = BeautifulSoup(
                description or "",
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )

            description = _clean_text(
                description
            )

            source_el = item.find(
                "source"
            )

            publisher = (
                source_el.text.strip()
                if (
                    source_el is not None
                    and source_el.text
                )
                else ""
            )

            if title and link:

                results.append({
                    "title": title,
                    "link": link,
                    "published": pub_date,
                    "publisher": publisher,
                    "description": description,
                })

        return results

    except Exception as exc:

        print(
            "Google News RSS error:",
            exc
        )

        return []


def _claim_keywords(claim: str):

    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "that",
        "this",
        "it",
        "as",
        "by",
        "from",
        "with",
        "at",
        "be",
        "been",
        "being",
        "will",
        "would",
        "could",
        "should",
        "can",
        "may",
        "according",
        "said",
        "says",
        "their",
        "his",
        "her",
        "its",
    }

    words = re.findall(
        r"[a-z0-9]+",
        claim.lower()
    )

    return {
        word
        for word in words
        if len(word) >= 3
        and word not in stopwords
    }


def _official_seed_urls(claim: str):

    lower = claim.lower()

    urls = []

    if (
        "narendra modi" in lower
        and "prime minister" in lower
        and (
            "india" in lower
            or "indian" in lower
        )
    ):

        urls.extend([
            (
                "PM India - Know the PM",
                "https://www.pmindia.gov.in/en/pms-profile/"
            ),
            (
                "PM India - Union Council portfolios",
                "https://www.pmindia.gov.in/en/news_updates/portfolios-of-the-union-council-of-ministers-2/"
            ),
            (
                "President of India - 9 June 2024 appointment",
                "https://www.presidentofindia.gov.in/press_releases/press-communique-17"
            ),
        ])

    if (
        "isro" in lower
        or "chandrayaan" in lower
    ):

        urls.append(
            (
                "ISRO official website",
                "https://www.isro.gov.in/"
            )
        )

    return urls


def _source_score(item, claim_words):

    domain = _domain_from_url(
        item.get("url", "")
    )

    title_words = set(
        re.findall(
            r"[a-z0-9]+",
            item.get(
                "title",
                ""
            ).lower()
        )
    )

    text_words = set(
        re.findall(
            r"[a-z0-9]+",
            item.get(
                "article_text",
                ""
            ).lower()
        )
    )

    score = 0

    if any(
        domain == d
        or domain.endswith("." + d)
        for d in AUTHORITATIVE_DOMAINS
    ):
        score += 100

    score += min(
        len(claim_words & title_words) * 4,
        25
    )

    score += min(
        len(claim_words & text_words) * 1.5,
        35
    )

    if item.get("article_text"):
        score += 20

    return score


def search_evidence(
    claim: str,
    max_records: int = 5
):

    if not claim or not claim.strip():
        return []

    claim = claim.strip()

    print("\n" + "=" * 70)
    print("EVIDENCE SEARCH")
    print("=" * 70)

    print(
        "Claim:",
        claim
    )

    claim_words = _claim_keywords(
        claim
    )

    candidates = []

    seen_urls = set()

    # --------------------------------------------------
    # 1. OFFICIAL SOURCES
    # --------------------------------------------------

    for title, url in _official_seed_urls(
        claim
    ):

        if url in seen_urls:
            continue

        text = _fetch_page_text(
            url
        )

        if text:

            candidates.append({

                "title": title,

                "url": url,

                "source": _domain_from_url(
                    url
                ),

                "date": "",

                "snippet": text[:1000],

                "article_text": text,

                "evidence_text": text,

            })

            seen_urls.add(url)

    # --------------------------------------------------
    # 2. GOOGLE NEWS SEARCHES
    # --------------------------------------------------

    keywords = sorted(
        claim_words,
        key=len,
        reverse=True
    )[:10]

    queries = [
        claim,
    ]

    if keywords:

        queries.append(
            " ".join(keywords)
        )

    for query in queries:

        rss_results = _google_news_rss(
            query
        )

        print(
            "RSS results:",
            len(rss_results)
        )

        for rss in rss_results[:10]:

            rss_link = rss.get(
                "link",
                ""
            )

            if not rss_link:
                continue

            # ------------------------------------------
            # Try to resolve original publisher URL
            # ------------------------------------------

            final_url = rss_link

            try:

                response = requests.get(
                    rss_link,
                    headers=HEADERS,
                    timeout=15,
                    allow_redirects=True,
                )

                if response.url:
                    final_url = response.url

            except Exception as exc:

                print(
                    "URL resolution failed:",
                    exc
                )

            domain = _domain_from_url(
                final_url
            )

            # If the URL is still Google News,
            # keep the RSS URL as evidence source.
            if not domain:

                domain = "news.google.com"

            if final_url in seen_urls:
                continue

            # ------------------------------------------
            # Try publisher page
            # ------------------------------------------

            article_text = ""

            if (
                domain != "news.google.com"
                and "google.com" not in domain
            ):

                article_text = _fetch_page_text(
                    final_url
                )

            # ------------------------------------------
            # IMPORTANT FALLBACK:
            # Use RSS description when article page
            # cannot be scraped.
            # ------------------------------------------

            snippet = _clean_text(
                rss.get(
                    "description",
                    ""
                )
            )

            if not article_text:

                article_text = snippet

            # Do NOT discard the result anymore.
            # RSS description itself is usable evidence.

            if not article_text:

                print(
                    "Skipping result with no text:",
                    rss.get("title", "")
                )

                continue

            source_type = (
                "authoritative"
                if any(
                    domain == d
                    or domain.endswith("." + d)
                    for d in AUTHORITATIVE_DOMAINS
                )
                else "news"
            )

            evidence_text = (
                f"Title: {rss.get('title', '')}\n"
                f"Publisher: "
                f"{rss.get('publisher', '') or domain}\n"
                f"Published: "
                f"{rss.get('published', '')}\n"
                f"URL: {final_url}\n"
                f"Content: {article_text}"
            )

            candidates.append({

                "title": rss.get(
                    "title",
                    ""
                ),

                "url": final_url,

                "source": (
                    rss.get(
                        "publisher",
                        ""
                    )
                    or domain
                ),

                "date": rss.get(
                    "published",
                    ""
                ),

                "snippet": snippet,

                "article_text": article_text,

                "evidence_text": evidence_text,

                "source_type": source_type,
            })

            seen_urls.add(
                final_url
            )

    # --------------------------------------------------
    # 3. RANK RESULTS
    # --------------------------------------------------

    candidates.sort(
        key=lambda item:
            _source_score(
                item,
                claim_words
            ),
        reverse=True,
    )

    results = candidates[
        :max_records
    ]

    print(
        "\nTotal usable evidence:",
        len(results)
    )

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            f"\nEvidence {index}:"
        )

        print(
            "Title:",
            item.get(
                "title",
                ""
            )
        )

        print(
            "Source:",
            item.get(
                "source",
                ""
            )
        )

        print(
            "URL:",
            item.get(
                "url",
                ""
            )
        )

    return results