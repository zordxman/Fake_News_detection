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
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
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

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script", "style", "noscript", "nav",
            "header", "footer", "form", "svg"
        ]):
            tag.decompose()

        parts = []
        for element in soup.find_all(["h1", "h2", "h3", "p", "article"]):
            value = _clean_text(element.get_text(" ", strip=True))
            if value:
                parts.append(value)

        # Remove repeated text while preserving order.
        unique = []
        seen = set()
        for value in parts:
            if value not in seen:
                unique.append(value)
                seen.add(value)

        return " ".join(unique)[:12000]

    except Exception:
        return ""


def _google_news_rss(query: str):
    encoded = urllib.parse.quote_plus(query)
    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)
        results = []

        for item in root.findall(".//item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()

            source_el = item.find("source")
            publisher = (
                source_el.text.strip()
                if source_el is not None and source_el.text
                else ""
            )

            if title and link:
                results.append({
                    "title": title,
                    "link": link,
                    "published": pub_date,
                    "publisher": publisher,
                })

        return results

    except Exception:
        return []


def _claim_keywords(claim: str):
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "has", "have",
        "had", "to", "of", "in", "on", "for", "and", "or", "that",
        "this", "it", "as", "by", "from", "with", "at", "be", "been",
        "being", "will", "would", "could", "should", "can", "may",
        "according", "said", "says", "their", "his", "her", "its",
    }

    words = re.findall(r"[a-z0-9]+", claim.lower())
    return {w for w in words if len(w) >= 3 and w not in stopwords}


def _official_seed_urls(claim: str):
    """
    Small set of high-value official fallbacks.

    These are not hard-coded verdicts. They are official documents/pages
    that can be fetched and supplied as evidence to the LLM.
    """
    lower = claim.lower()
    urls = []

    # Current office-holder / PM claims.
    if (
        "narendra modi" in lower
        and "prime minister" in lower
        and ("india" in lower or "indian" in lower)
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

    # ISRO / Chandrayaan claims.
    if "isro" in lower or "chandrayaan" in lower:
        urls.append((
            "ISRO official website",
            "https://www.isro.gov.in/"
        ))

    return urls


def _source_score(item, claim_words):
    domain = _domain_from_url(item.get("url", ""))
    title_words = set(
        re.findall(r"[a-z0-9]+", item.get("title", "").lower())
    )
    text_words = set(
        re.findall(r"[a-z0-9]+", item.get("text", "").lower())
    )

    score = 0

    if any(
        domain == d or domain.endswith("." + d)
        for d in AUTHORITATIVE_DOMAINS
    ):
        score += 100

    score += min(len(claim_words & title_words) * 4, 25)
    score += min(len(claim_words & text_words) * 1.5, 35)

    if item.get("text"):
        score += 20

    return score


def search_evidence(claim: str, max_records: int = 5):
    """
    Retrieve external evidence for a claim.

    Strategy:
      1. Fetch known authoritative pages when the claim matches
         a high-confidence official-source pattern.
      2. Search Google News RSS for the exact claim.
      3. Search Google News RSS using a shorter keyword query.
      4. Rank authoritative and text-relevant sources first.
    """
    if not claim or not claim.strip():
        return []

    claim = claim.strip()
    claim_words = _claim_keywords(claim)
    candidates = []
    seen_urls = set()

    # 1. Direct official fallbacks.
    for title, url in _official_seed_urls(claim):
        if url in seen_urls:
            continue

        text = _fetch_page_text(url)

        if text:
            candidates.append({
                "title": title,
                "url": url,
                "publisher_url": url,
                "publisher": _domain_from_url(url),
                "published": "",
                "text": text,
                "source_type": "authoritative",
            })
            seen_urls.add(url)

    # 2. Exact claim search.
    queries = [
        f'"{claim}"',
        claim,
    ]

    # 3. Short keyword search for cases where exact wording differs
    # from the official source.
    keywords = sorted(claim_words, key=len, reverse=True)[:10]
    if keywords:
        queries.append(" ".join(keywords))

    for query in queries:
        for rss in _google_news_rss(query)[:10]:
            rss_link = rss["link"]

            try:
                response = requests.get(
                    rss_link,
                    headers=HEADERS,
                    timeout=15,
                    allow_redirects=True,
                )
                final_url = response.url or rss_link
            except Exception:
                final_url = rss_link

            domain = _domain_from_url(final_url)

            if not domain or final_url in seen_urls:
                continue

            text = _fetch_page_text(final_url)

            source_type = (
                "authoritative"
                if any(
                    domain == d or domain.endswith("." + d)
                    for d in AUTHORITATIVE_DOMAINS
                )
                else "news"
            )

            candidates.append({
                "title": rss["title"],
                "url": final_url,
                "publisher_url": final_url,
                "publisher": rss["publisher"] or domain,
                "published": rss["published"],
                "text": text,
                "source_type": source_type,
            })
            seen_urls.add(final_url)

    candidates.sort(
        key=lambda item: _source_score(item, claim_words),
        reverse=True,
    )

    results = []
    for item in candidates:
        # Do not send empty pages to the verifier.
        if not item.get("text"):
            continue

        results.append(item)

        if len(results) >= max_records:
            break

    return results
