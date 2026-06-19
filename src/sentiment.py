"""
sentiment.py
------------
Sentiment classification using DistilBERT fine-tuned on SST-2.

Model : distilbert-base-uncased-finetuned-sst-2-english
        Lightweight BERT variant — fast, accurate, ideal for news sentiment.

What  : Takes article text → returns Positive/Negative + confidence score.
Why   : DistilBERT is 40% smaller than BERT but retains 97% of performance.
"""

from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer
)
import torch
import logging

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_NAME      = "distilbert-base-uncased-finetuned-sst-2-english"
MAX_INPUT_TOKENS = 512    # DistilBERT's hard token limit
LABELS          = ["Negative", "Positive"]   # SST-2 label mapping

# ── Module-level model cache ──────────────────────────────────────────────────
_model     = None
_tokenizer = None


def _load_model():
    """
    Lazy-load DistilBERT model and tokenizer.
    Much smaller than BART (~250MB) — loads in seconds.
    """
    global _model, _tokenizer

    if _model is None or _tokenizer is None:
        logger.info("Loading DistilBERT sentiment model...")
        _tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
        _model     = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.eval()   # Set to evaluation mode — disables dropout layers
        logger.info("✅ DistilBERT model loaded successfully.")

    return _model, _tokenizer


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_sentiment(text: str) -> dict:
    """
    Classify sentiment of news article text.

    Args:
        text: Raw article text (from scraper.py)

    Returns:
        dict with keys:
            label      : str   — "Positive" or "Negative"
            confidence : float — confidence score 0.0 to 1.0
            scores     : dict  — raw scores for both labels

    Raises:
        ValueError: If text is empty.
        TypeError:  If text is not a string.
    """

    # ── Input validation ──────────────────────────────────────────────────────
    if not isinstance(text, str):
        raise TypeError(f"Expected string, got {type(text).__name__}.")

    text = text.strip()

    if not text:
        raise ValueError("Cannot analyze sentiment of empty text.")

    logger.info("Analyzing sentiment of %d characters...", len(text))

    # ── Load model ────────────────────────────────────────────────────────────
    model, tokenizer = _load_model()

    # ── Tokenize ──────────────────────────────────────────────────────────────
    # DistilBERT reads the first 512 tokens — enough for most news articles
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=MAX_INPUT_TOKENS,
        truncation=True,
        padding=True
    )

    # ── Run inference ─────────────────────────────────────────────────────────
    with torch.no_grad():    # Disables gradient tracking — saves memory
        outputs = model(**inputs)

    # ── Process output ────────────────────────────────────────────────────────
    # Logits are raw scores → softmax converts to probabilities (sum to 1.0)
    probabilities = torch.softmax(outputs.logits, dim=1)[0]

    neg_score = probabilities[0].item()
    pos_score = probabilities[1].item()

    # Pick the label with highest probability
    if pos_score > neg_score:
        label      = "Positive"
        confidence = pos_score
    else:
        label      = "Negative"
        confidence = neg_score

    logger.info(
        "✅ Sentiment: %s (%.1f%% confident)",
        label, confidence * 100
    )

    return {
        "label":      label,
        "confidence": round(confidence, 4),
        "scores": {
            "Positive": round(pos_score, 4),
            "Negative": round(neg_score, 4),
        }
    }