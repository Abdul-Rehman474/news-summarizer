"""
test_pipeline.py
----------------
Manual test for scraper.py.
Run from project root: python -m tests.test_pipeline
"""

from src.scraper import scrape_article

TEST_URLS = [
    "https://www.bbc.com/news/articles/c5y32y2g2eeo",
    "https://techcrunch.com/2024/04/23/google-gemini-1-5-pro/",
]

EDGE_CASES = [
    "",
    "not-a-url",
    "https://thisdomaindoesnotexist99999.com",
]


def test_valid_urls():
    for url in TEST_URLS:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        try:
            result = scrape_article(url)
            print(f"  ✅ Title   : {result['title'][:80]}")
            print(f"  ✅ Method  : {result['method']}")
            print(f"  ✅ Length  : {len(result['text'])} chars")
            print(f"  ✅ Preview : {result['text'][:200]}...")
        except ValueError as e:
            print(f"  ⚠️  Could not scrape: {e}")


def test_edge_cases():
    print(f"\n{'='*60}")
    print("Testing edge cases...")
    for url in EDGE_CASES:
        try:
            scrape_article(url)
            print(f"  ❌ Should have failed for: '{url}'")
        except (ValueError, TypeError) as e:
            print(f"  ✅ Correctly rejected '{url[:40]}': {e}")


if __name__ == "__main__":
    test_valid_urls()
    test_edge_cases()