"""
ner.py
------
Named Entity Recognition using spaCy.

Model : en_core_web_sm
        Small English model — fast, no GPU needed.

What  : Takes article text → extracts persons, organizations, locations.
Why   : Helps readers instantly see WHO and WHERE a story is about.
"""

import spacy
import logging

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── Entity types we care about ────────────────────────────────────────────────
# spaCy has 18 entity types — we filter to the most useful for news
ENTITY_TYPES = {
    "PERSON":   "People",
    "ORG":      "Organizations",
    "GPE":      "Locations",       # GPE = Geo-Political Entity (cities, countries)
    "LOC":      "Locations",       # LOC = Natural locations (rivers, mountains)
    "NORP":     "Groups",          # Nationalities, religions, political groups
}

# ── Module-level model cache ──────────────────────────────────────────────────
_nlp = None


def _load_model():
    """
    Lazy-load spaCy English model.
    Tiny (~12MB) — loads in under 1 second.
    """
    global _nlp

    if _nlp is None:
        logger.info("Loading spaCy en_core_web_sm model...")
        _nlp = spacy.load("en_core_web_sm")
        logger.info("✅ spaCy model loaded successfully.")

    return _nlp


# ── Public API ────────────────────────────────────────────────────────────────

def extract_entities(text: str) -> dict:
    """
    Extract named entities from news article text.

    Args:
        text: Raw article text (from scraper.py)

    Returns:
        dict with keys:
            people        : list — person names found
            organizations : list — org names found
            locations     : list — places found
            groups        : list — nationalities/political groups found
            all_entities  : list — all entities with type and text

    Raises:
        ValueError: If text is empty.
        TypeError:  If text is not a string.
    """

    # ── Input validation ──────────────────────────────────────────────────────
    if not isinstance(text, str):
        raise TypeError(f"Expected string, got {type(text).__name__}.")

    text = text.strip()

    if not text:
        raise ValueError("Cannot extract entities from empty text.")

    logger.info("Extracting entities from %d characters...", len(text))

    # ── Load model ────────────────────────────────────────────────────────────
    nlp = _load_model()

    # ── Run NER ───────────────────────────────────────────────────────────────
    doc = nlp(text)

    # ── Collect entities ──────────────────────────────────────────────────────
    people        = []
    organizations = []
    locations     = []
    groups        = []
    all_entities  = []

    seen = set()    # Avoid duplicates

    for ent in doc.ents:

        # Only keep entity types we care about
        if ent.label_ not in ENTITY_TYPES:
            continue

        name = ent.text.strip()

        # Skip duplicates and very short strings
        if name in seen or len(name) < 2:
            continue

        seen.add(name)

        # Add to correct category
        if ent.label_ == "PERSON":
            people.append(name)
        elif ent.label_ == "ORG":
            organizations.append(name)
        elif ent.label_ in ("GPE", "LOC"):
            locations.append(name)
        elif ent.label_ == "NORP":
            groups.append(name)

        all_entities.append({
            "text":  name,
            "label": ent.label_,
            "type":  ENTITY_TYPES[ent.label_]
        })

    logger.info(
        "✅ Found %d entities — %d people, %d orgs, %d locations, %d groups",
        len(all_entities), len(people),
        len(organizations), len(locations), len(groups)
    )

    return {
        "people":        people,
        "organizations": organizations,
        "locations":     locations,
        "groups":        groups,
        "all_entities":  all_entities,
    }