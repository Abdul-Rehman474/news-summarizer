"""
scraper.py
----------
Extracts clean article text from a given news URL.

Strategy:
  1. Try newspaper3k first (fast, handles most news sites natively).
  2. Fall back to requests + BeautifulSoup if newspaper3k fails or
     returns too little text (e.g., paywalled / JS-heavy pages).

Returns a dict with: title, text, authors, publish_date, source_url
"""

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from newspaper import ArticleException
import logging

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_TEXT_LENGTH = 200        # Minimum characters to consider extraction valid
REQUEST_TIMEOUT = 10         # Seconds before HTTP request gives up
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ── Primary extractor: newspaper3k ───────────────────────────────────────────

def _extract_with_newspaper(url: str) -> dict | None:
    """
    Attempt extraction using newspaper3k.
    Returns a result dict on success, None on failure.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text.strip()

        if len(text) < MIN_TEXT_LENGTH:
            logger.warning(
                "newspaper3k returned too little text (%d chars). "
                "Will try fallback.", len(text)
            )
            return None

        return {
            "title":        article.title or "No title found",
            "text":         text,
            "authors":      article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "source_url":   url,
            "method":       "newspaper3k",
        }

    except ArticleException as e:
        logger.warning("newspaper3k ArticleException: %s", e)
        return None
    except Exception as e:
        logger.warning("newspaper3k unexpected error: %s", e)
        return None


# ── Fallback extractor: requests + BeautifulSoup ──────────────────────────────

def _extract_with_bs4(url: str) -> dict | None:
    """
    Fallback: fetch raw HTML with requests, parse with BeautifulSoup.
    Targets <article>, <p> tags — works on most news sites.
    Returns a result dict on success, None on failure.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove noise: scripts, styles, nav, ads
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()

        # Prefer <article> block; fall back to all <p> tags
        article_block = soup.find("article")
        if article_block:
            paragraphs = article_block.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        text = " ".join(p.get_text(separator=" ").strip() for p in paragraphs)
        text = " ".join(text.split())

        if len(text) < MIN_TEXT_LENGTH:
            logger.warning(
                "BeautifulSoup also returned too little text (%d chars).",
                len(text)
            )
            return None

        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else "No title found"

        return {
            "title":        title,
            "text":         text,
            "authors":      [],
            "publish_date": None,
            "source_url":   url,
            "method":       "beautifulsoup",
        }

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to URL: %s", url)
        return None
    except requests.exceptions.Timeout:
        logger.error("Request timed out for URL: %s", url)
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error %s for URL: %s", e.response.status_code, url)
        return None
    except Exception as e:
        logger.error("BeautifulSoup unexpected error: %s", e)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def scrape_article(url: str) -> dict:
    """
    Main entry point. Scrape a news article from the given URL.

    Args:
        url: A fully-qualified URL string (e.g. 'https://bbc.com/news/...')

    Returns:
        dict with keys: title, text, authors, publish_date, source_url, method

    Raises:
        ValueError: If the URL is empty or both extractors fail.
        TypeError:  If url is not a string.
    """
    if not isinstance(url, str):
        raise TypeError(f"Expected a string URL, got {type(url).__name__}.")

    url = url.strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    if not url.startswith(("http://", "https://")):
        raise ValueError(
            f"Invalid URL (must start with http:// or https://): '{url}'"
        )

    logger.info("Scraping URL: %s", url)

    result = _extract_with_newspaper(url)

    if result is None:
        logger.info("Falling back to BeautifulSoup for: %s", url)
        result = _extract_with_bs4(url)

    if result is None:
        raise ValueError(
            f"Could not extract article text from: {url}\n"
            "Possible reasons: paywall, JavaScript-rendered page, "
            "bot protection, or insufficient article content."
        )

    logger.info(
        "✅ Extracted %d characters via %s | Title: '%s'",
        len(result["text"]), result["method"], result["title"]
    )
    return result