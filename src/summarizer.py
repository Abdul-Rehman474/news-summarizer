"""
summarizer.py
-------------
Abstractive news article summarization using BART.

Model : facebook/bart-large-cnn
        Pretrained on CNN/DailyMail dataset — ideal for news articles.

What  : Takes long article text → returns a concise 3-5 sentence summary.
Why   : Abstractive = generates NEW sentences (not copy-paste from article).
"""

from transformers import BartForConditionalGeneration, BartTokenizer
import logging

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_NAME     = "facebook/bart-large-cnn"
MAX_INPUT_TOKENS = 1024   # BART's hard token limit
MIN_SUM_TOKENS   = 60     # Minimum summary length in tokens
MAX_SUM_TOKENS   = 180    # Maximum summary length in tokens

# ── Module-level model cache ──────────────────────────────────────────────────
# Loaded once, reused forever — avoids 30s reload on every request
_model     = None
_tokenizer = None


def _load_model():
    """
    Lazy-load BART model and tokenizer.
    First call downloads ~1.6GB (cached by HuggingFace after that).
    """
    global _model, _tokenizer

    if _model is None or _tokenizer is None:
        logger.info("Loading BART model — this takes ~30s on first run...")
        _tokenizer = BartTokenizer.from_pretrained(MODEL_NAME)
        _model     = BartForConditionalGeneration.from_pretrained(MODEL_NAME)
        logger.info("✅ BART model loaded successfully.")

    return _model, _tokenizer


# ── Public API ────────────────────────────────────────────────────────────────

def summarize(text: str) -> dict:
    """
    Summarize a news article using BART.

    Args:
        text: Raw article text (from scraper.py)

    Returns:
        dict with keys:
            summary      : str — the generated summary
            input_chars  : int — length of input text
            output_chars : int — length of generated summary

    Raises:
        ValueError: If text is empty or too short.
        TypeError:  If text is not a string.
    """

    # ── Input validation ──────────────────────────────────────────────────────
    if not isinstance(text, str):
        raise TypeError(f"Expected string, got {type(text).__name__}.")

    text = text.strip()

    if not text:
        raise ValueError("Cannot summarize empty text.")

    if len(text) < 100:
        raise ValueError(
            f"Text too short to summarize ({len(text)} chars). "
            "Minimum 100 characters required."
        )

    logger.info("Summarizing %d characters...", len(text))

    # ── Load model ────────────────────────────────────────────────────────────
    model, tokenizer = _load_model()

    # ── Tokenize input ────────────────────────────────────────────────────────
    # Converts text → token IDs BART understands
    # truncation=True cuts off at MAX_INPUT_TOKENS safely
    inputs = tokenizer(
        text,
        return_tensors="pt",      # pt = PyTorch tensors
        max_length=MAX_INPUT_TOKENS,
        truncation=True
    )

    # ── Generate summary ──────────────────────────────────────────────────────
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=MAX_SUM_TOKENS,
        min_length=MIN_SUM_TOKENS,
        length_penalty=2.0,       # Encourages longer summaries
        num_beams=4,              # Beam search — tries 4 paths, picks best
        early_stopping=True       # Stop when all beams reach end token
    )

    # ── Decode output ─────────────────────────────────────────────────────────
    # Converts token IDs back to readable text
    summary = tokenizer.decode(
        summary_ids[0],
        skip_special_tokens=True  # Removes <s>, </s> tokens from output
    ).strip()

    logger.info("✅ Summary generated (%d chars).", len(summary))

    return {
        "summary":      summary,
        "input_chars":  len(text),
        "output_chars": len(summary),
    }