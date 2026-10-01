import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse


GOOGLE_NEWS_URL = "https://news.google.com/rss/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------
# CLEAN SEARCH QUERY
# ---------------------------------------------------------

def clean_query(claim):

    query = claim.replace('"', '')
    query = query.replace("'", '')
    query = query.replace("“", "")
    query = query.replace("”", "")

    query = " ".join(query.split())

    words = query.split()

    # Keep search query manageable
    if len(words) > 15:
        words = words[:15]

    return " ".join(words)


# ---------------------------------------------------------
# RESOLVE GOOGLE NEWS URL
# ---------------------------------------------------------

def resolve_article_url(google_url):
    if not google_url:
        return None

    try:
        from googlenewsdecoder import gnewsdecoder
    except ImportError:
        print("googlenewsdecoder is not installed; using Google News URL.")
        return google_url

    try:
        result = gnewsdecoder(google_url, interval=1)

        if not result.get("success"):
            print("Could not decode Google News URL; using original URL.")
            return google_url

        article_url = result.get("decoded_url")
        return article_url or google_url

    except Exception as e:
        print("Google News URL decoding failed:", e)
        return google_url


# ---------------------------------------------------------
# EXTRACT ARTICLE TEXT
# ---------------------------------------------------------

def extract_article_text(url):

    if not url:
        return ""

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # -------------------------------------------------
        # REMOVE UNNECESSARY HTML
        # -------------------------------------------------

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "noscript",
            "iframe"
        ]):

            tag.decompose()

        paragraphs = []

        # -------------------------------------------------
        # FIRST: TRY ARTICLE TAG
        # -------------------------------------------------

        article_tags = soup.find_all("article")

        for article in article_tags:

            for p in article.find_all("p"):

                text = p.get_text(
                    " ",
                    strip=True
                )

                if len(text) >= 40:
                    paragraphs.append(text)

        # -------------------------------------------------
        # SECOND: ALL PARAGRAPHS
        # -------------------------------------------------

        if not paragraphs:

            for p in soup.find_all("p"):

                text = p.get_text(
                    " ",
                    strip=True
                )

                if len(text) >= 40:
                    paragraphs.append(text)

        # -------------------------------------------------
        # REMOVE DUPLICATES
        # -------------------------------------------------

        unique_paragraphs = []

        for paragraph in paragraphs:

            if paragraph not in unique_paragraphs:
                unique_paragraphs.append(paragraph)

        article_text = " ".join(
            unique_paragraphs
        )

        # -------------------------------------------------
        # CLEAN TEXT
        # -------------------------------------------------

        article_text = re.sub(
            r"\s+",
            " ",
            article_text
        ).strip()

        # -------------------------------------------------
        # LIMIT LENGTH
        # -------------------------------------------------

        if len(article_text) > 6000:

            article_text = article_text[:6000]

        print(
            "Extracted article text:",
            len(article_text),
            "characters"
        )

        return article_text

    except Exception as e:

        print(
            "Article extraction failed:",
            e
        )

        return ""


# ---------------------------------------------------------
# SEARCH GOOGLE NEWS
# ---------------------------------------------------------

def search_evidence(claim, max_records=5):

    query = clean_query(claim)

    print("\nSearch query:")
    print(query)

    params = {
        "q": query,
        "hl": "en-IN",
        "gl": "IN",
        "ceid": "IN:en"
    }

    try:

        response = requests.get(
            GOOGLE_NEWS_URL,
            params=params,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "Google News search failed:",
            e
        )

        return []

    # -----------------------------------------------------
    # PARSE RSS
    # -----------------------------------------------------

    try:

        root = ET.fromstring(
            response.content
        )

    except Exception as e:

        print(
            "RSS parsing failed:",
            e
        )

        return []

    results = []

    items = root.findall(".//item")

    # Limit number of articles
    items = items[:max_records]

    # -----------------------------------------------------
    # PROCESS EACH RESULT
    # -----------------------------------------------------

    for index, item in enumerate(
        items,
        start=1
    ):

        title = item.findtext(
            "title",
            ""
        )

        google_url = item.findtext(
            "link",
            ""
        )

        pub_date = item.findtext(
            "pubDate",
            ""
        )

        description = item.findtext(
            "description",
            ""
        )

        # -------------------------------------------------
        # SOURCE
        # -------------------------------------------------

        source_element = item.find(
            "source"
        )

        if source_element is not None:

            source_name = (
                source_element.text
                or "Unknown"
            )

        else:

            source_name = "Unknown"

        # -------------------------------------------------
        # CLEAN DESCRIPTION
        # -------------------------------------------------

        clean_description = re.sub(
            r"<[^>]+>",
            "",
            description
        )

        clean_description = (
            BeautifulSoup(
                clean_description,
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )
        )

        # -------------------------------------------------
        # PRINT RESULT
        # -------------------------------------------------

        print("\n" + "=" * 70)

        print(
            f"RESULT {index}"
        )

        print(
            "Title:",
            title
        )

        print(
            "Publisher:",
            source_name
        )

        # -------------------------------------------------
        # RESOLVE ORIGINAL ARTICLE
        # -------------------------------------------------

        print("\nResolving article URL...")

        article_url = resolve_article_url(
            google_url
        )

        # -------------------------------------------------
        # EXTRACT ARTICLE
        # -------------------------------------------------

        article_text = ""

        if article_url:

            print(
                "\nFetching publisher article..."
            )

            print(
                article_url
            )

            article_text = extract_article_text(
                article_url
            )

        else:

            print(
                "Publisher URL could not be found."
            )

        # -------------------------------------------------
        # EVIDENCE TEXT
        # -------------------------------------------------

        evidence_text = f"""
Title: {title}

Publisher: {source_name}

Date: {pub_date}

Description:
{clean_description}

Article:
{article_text}
""".strip()

        # -------------------------------------------------
        # SAVE RESULT
        # -------------------------------------------------

        results.append({

            "title": title,

            "url": (
                article_url
                if article_url
                else google_url
            ),

            "source": source_name,

            "date": pub_date,

            "snippet": clean_description,

            "article_text": article_text,

            "evidence_text": evidence_text
        })

    return results