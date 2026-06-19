"""
app.py
------
Sentiment-Aware News Summarizer — Gen Z Edition
Themes: Neon, Pastel, Dark, Light, Vaporwave
Features: Theme picker, copy button, article history, word count,
          reading time, sentiment chart, entity tags
"""

import streamlit as st
import time
import plotly.graph_objects as go
from src.scraper    import scrape_article
from src.summarizer import summarize
from src.sentiment  import analyze_sentiment
from src.ner        import extract_entities

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NewsAI ✨",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "🌙 Neon Dark": {
        "bg":         "#0d0d0d",
        "card":       "#1a1a2e",
        "accent":     "#e94560",
        "accent2":    "#0f3460",
        "text":       "#eaeaea",
        "subtext":    "#a0a0b0",
        "positive":   "#00ff88",
        "negative":   "#ff4466",
        "border":     "#e9456033",
        "tag_bg":     "#e9456022",
        "font":       "Courier New, monospace",
    },
    "🌸 Soft Pastel": {
        "bg":         "#fdf6f0",
        "card":       "#fff0f5",
        "accent":     "#ff6eb4",
        "accent2":    "#a78bfa",
        "text":       "#1a1a1a",
        "subtext":    "#555555",
        "positive":   "#4ade80",
        "negative":   "#f87171",
        "border":     "#ff6eb433",
        "tag_bg":     "#ff6eb415",
        "font":       "Georgia, serif",
    },
    "🌊 Vaporwave": {
        "bg":         "#1a0533",
        "card":       "#2d0b5e",
        "accent":     "#ff71ce",
        "accent2":    "#01cdfe",
        "text":       "#fffaf0",
        "subtext":    "#b39ddb",
        "positive":   "#05ffa1",
        "negative":   "#ff71ce",
        "border":     "#ff71ce33",
        "tag_bg":     "#ff71ce15",
        "font":       "Trebuchet MS, sans-serif",
    },
    "🤍 Clean Light": {
        "bg":         "#f8fafc",
        "card":       "#ffffff",
        "accent":     "#6366f1",
        "accent2":    "#8b5cf6",
        "text":       "#0f172a",
        "subtext":    "#374151",
        "positive":   "#22c55e",
        "negative":   "#ef4444",
        "border":     "#6366f133",
        "tag_bg":     "#6366f110",
        "font":       "Inter, sans-serif",
    },
    "🌿 Matcha": {
        "bg":         "#1a1f1a",
        "card":       "#1e2a1e",
        "accent":     "#86efac",
        "accent2":    "#4ade80",
        "text":       "#ecfdf5",
        "subtext":    "#86efac99",
        "positive":   "#4ade80",
        "negative":   "#fca5a5",
        "border":     "#86efac33",
        "tag_bg":     "#86efac15",
        "font":       "monospace",
    },
}

# ── Cache models ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_all_models():
    from src.summarizer import _load_model as s
    from src.sentiment  import _load_model as sent
    from src.ner        import _load_model as n
    s(); sent(); n()
    return True

# ── Session state init ────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []    # List of past results
if "theme" not in st.session_state:
    st.session_state.theme = "🌙 Neon Dark"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✨ NewsAI")
    st.markdown("---")

    # Theme picker
    st.markdown("### 🎨 Pick Your Vibe")
    selected_theme = st.radio(
        label="theme",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme),
        label_visibility="collapsed"
    )
    st.session_state.theme = selected_theme
    T = THEMES[selected_theme]

    st.markdown("---")

    # History
    st.markdown("### 🕓 Recent Articles")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            if st.button(
                f"📰 {h['title'][:35]}...",
                key=f"hist_{i}",
                use_container_width=True
            ):
                st.session_state.prefill_url = h["url"]
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No articles yet. Analyze something!")

    st.markdown("---")
    st.caption("Built by Abdul Rehman 🚀")

# ── Get active theme ──────────────────────────────────────────────────────────
T = THEMES[st.session_state.theme]

# ── Inject CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Global */
html, body, [class*="css"], p, span, div, h1, h2, h3, label {{
    font-family: {T['font']};
    background-color: transparent;
    color: {T['text']} !important;
}}

.stApp {{
    background-color: {T['bg']} !important;
}}

p, span, li, div {{
    color: {T['text']} !important;
}}

/* Main background */
.stApp {{
    background-color: {T['bg']} !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: {T['card']} !important;
    border-right: 1px solid {T['border']} !important;
}}

/* Cards */
.news-card {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 4px 24px {T['border']};
}}

/* Accent heading */
.accent-text {{
    color: {T['accent']};
    font-weight: 700;
}}

/* Tag pills */
.entity-tag {{
    display: inline-block;
    background: {T['tag_bg']};
    border: 1px solid {T['accent']};
    color: {T['accent']};
    border-radius: 999px;
    padding: 4px 14px;
    margin: 4px;
    font-size: 0.85rem;
    font-weight: 600;
}}

/* Stat boxes */
.stat-box {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}}

.stat-number {{
    font-size: 2rem;
    font-weight: 700;
    color: {T['accent']};
}}

.stat-label {{
    font-size: 0.8rem;
    color: {T['subtext']};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* Title */
.hero-title {{
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, {T['accent']}, {T['accent2']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}}

.hero-sub {{
    color: {T['subtext']};
    font-size: 1.1rem;
    margin-top: 8px;
}}

/* Sentiment badge */
.sentiment-positive {{
    background: {T['positive']}22;
    color: {T['positive']};
    border: 1px solid {T['positive']};
    border-radius: 999px;
    padding: 6px 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}}

.sentiment-negative {{
    background: {T['negative']}22;
    color: {T['negative']};
    border: 1px solid {T['negative']};
    border-radius: 999px;
    padding: 6px 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}}

/* Buttons */
.stButton > button {{
    background: linear-gradient(135deg, {T['accent']}, {T['accent2']}) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: opacity 0.2s !important;
}}

.stButton > button:hover {{
    opacity: 0.85 !important;
}}

/* Input */
.stTextInput > div > div > input {{
    background: {T['card']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
}}

/* Divider */
hr {{
    border-color: {T['border']} !important;
}}

/* Text area for copy */
.stTextArea textarea {{
    background: {T['card']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    font-size: 0.95rem !important;
}}

/* Metric */
[data-testid="stMetric"] {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 16px;
}}

[data-testid="stMetricValue"] {{
    color: {T['accent']} !important;
}}

/* Expander */
[data-testid="stExpander"] {{
    background: {T['card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
}}

/* Radio buttons */
.stRadio label {{
    color: {T['text']} !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {T['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {T['accent']}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)


# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding: 2rem 0 1rem 0;">
    <div class="hero-title">📰 NewsAI</div>
    <div class="hero-sub">
        Drop a news URL. Get the vibe. No cap. ✨
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── URL Input ─────────────────────────────────────────────────────────────────
prefill = st.session_state.get("prefill_url", "")

col_input, col_btn = st.columns([5, 1])
with col_input:
    url = st.text_input(
        "🔗 Paste your news URL",
        value=prefill,
        placeholder="https://www.bbc.com/news/articles/...",
        label_visibility="collapsed"
    )
with col_btn:
    analyze_btn = st.button("✨ Analyze", type="primary", use_container_width=True)

# Clear prefill after use
if "prefill_url" in st.session_state:
    del st.session_state.prefill_url

st.markdown("---")

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyze_btn:

    # Validate
    if not url.strip():
        st.warning("⚠️ Paste a URL first bestie!")
        st.stop()
    if not url.startswith(("http://", "https://")):
        st.error("❌ That URL looks sus. Make sure it starts with https://")
        st.stop()

    # Load models
    with st.spinner("🤖 Warming up the AI..."):
        load_all_models()

    # ── Scrape ────────────────────────────────────────────────────────────────
    with st.spinner("🌐 Fetching article..."):
        try:
            article = scrape_article(url)
        except (ValueError, TypeError) as e:
            st.error(f"❌ Couldn't fetch that article: {e}")
            st.info("💡 Try a direct article URL (not a homepage).")
            st.stop()

    text = article["text"]
    word_count   = len(text.split())
    reading_time = max(1, round(word_count / 200))  # ~200 wpm

    st.success(f"✅ Got it! **{article['title']}**")

    # ── Run all 3 models ──────────────────────────────────────────────────────
    with st.spinner("🧠 Running AI pipeline..."):
        t0             = time.time()
        summary_result = summarize(text)
        sentiment_result = analyze_sentiment(text)
        ner_result     = extract_entities(text)
        elapsed        = round(time.time() - t0, 1)

    # ── Save to history ───────────────────────────────────────────────────────
    st.session_state.history.append({
        "url":       url,
        "title":     article["title"],
        "summary":   summary_result["summary"],
        "sentiment": sentiment_result["label"],
        "confidence": sentiment_result["confidence"],
    })

    # ════════════════════════════════════════════════════════════════════
    # STATS ROW
    # ════════════════════════════════════════════════════════════════════
    st.markdown("### 📊 Quick Stats")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{word_count}</div>
            <div class="stat-label">Words</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{reading_time}m</div>
            <div class="stat-label">Reading Time</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(ner_result['all_entities'])}</div>
            <div class="stat-label">Entities Found</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{elapsed}s</div>
            <div class="stat-label">AI Speed</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # LEFT + RIGHT COLUMNS
    # ════════════════════════════════════════════════════════════════════
    left, right = st.columns([3, 2])

    # ── LEFT: Summary ─────────────────────────────────────────────────
    with left:
        st.markdown(f"""
        <div class="news-card">
            <div class="accent-text">✍️ AI Summary</div>
        </div>
        """, unsafe_allow_html=True)

        summary_text = summary_result["summary"] if summary_result else text
        st.markdown(f"""
        <div class="news-card">
            <p style="line-height:1.8; font-size:1.05rem;">
                {summary_text}
            </p>
            <div style="color:{T['subtext']}; font-size:0.8rem; margin-top:12px;">
                📉 {summary_result['input_chars']} → {summary_result['output_chars']} chars
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Copy button
        st.markdown("**📋 Copy Summary**")
        st.text_area(
            label="copy",
            value=summary_text,
            height=120,
            label_visibility="collapsed",
            key="copy_summary"
        )
        st.caption("👆 Click inside → Ctrl+A → Ctrl+C to copy!")

    # ── RIGHT: Sentiment ──────────────────────────────────────────────
    with right:
        label      = sentiment_result["label"]
        confidence = sentiment_result["confidence"]
        pos_score  = sentiment_result["scores"]["Positive"]
        neg_score  = sentiment_result["scores"]["Negative"]

        badge_class = "sentiment-positive" if label == "Positive" else "sentiment-negative"
        emoji       = "😊" if label == "Positive" else "😟"

        st.markdown(f"""
        <div class="news-card">
            <div class="accent-text">💬 Sentiment Vibe</div>
            <br>
            <div style="text-align:center;">
                <div style="font-size:3rem;">{emoji}</div>
                <div class="{badge_class}">{label}</div>
                <div style="margin-top:12px; color:{T['subtext']};">
                    {confidence*100:.1f}% confident fr fr
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Plotly donut chart
        fig = go.Figure(go.Pie(
            labels=["Positive", "Negative"],
            values=[pos_score, neg_score],
            hole=0.65,
            marker=dict(
                colors=[T["positive"], T["negative"]],
                line=dict(color=T["bg"], width=2)
            ),
            textinfo="none",
            hovertemplate="%{label}: %{value:.1%}<extra></extra>"
        ))
        fig.update_layout(
            showlegend=True,
            height=220,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=T["text"]),
            legend=dict(
                font=dict(color=T["text"]),
                bgcolor="rgba(0,0,0,0)"
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # NAMED ENTITIES
    # ════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div class="news-card">
        <div class="accent-text">🏷️ Named Entities</div>
    </div>
    """, unsafe_allow_html=True)

    e1, e2, e3, e4 = st.columns(4)

    def render_tags(items, emoji, label):
        st.markdown(f"**{emoji} {label}**")
        if items:
            tags = "".join(
                f'<span class="entity-tag">{item}</span>'
                for item in items
            )
            st.markdown(tags, unsafe_allow_html=True)
        else:
            st.caption("None found")

    with e1:
        render_tags(ner_result["people"],        "👤", "People")
    with e2:
        render_tags(ner_result["organizations"], "🏢", "Orgs")
    with e3:
        render_tags(ner_result["locations"],     "📍", "Places")
    with e4:
        render_tags(ner_result["groups"],        "🌍", "Groups")

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════
    # ARTICLE METADATA
    # ════════════════════════════════════════════════════════════════════
    with st.expander("📄 Article Metadata"):
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown(f"**🖊️ Authors:** {', '.join(article['authors']) if article['authors'] else 'Not found'}")
            st.markdown(f"**📅 Date:** {article['publish_date'] or 'Not found'}")
            st.markdown(f"**🔧 Method:** {article['method']}")
        with mc2:
            st.markdown(f"**📏 Text length:** {len(text)} chars")
            st.markdown(f"**🔗 URL:** {url}")

    # ════════════════════════════════════════════════════════════════════
    # FULL ARTICLE TEXT
    # ════════════════════════════════════════════════════════════════════
    with st.expander("📖 View Full Article Text"):
        st.markdown(f"""
        <div style="line-height:1.8; color:{T['subtext']}; 
                    font-size:0.95rem; max-height:400px; 
                    overflow-y:auto; padding:8px;">
            {text}
        </div>
        """, unsafe_allow_html=True)

# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown(f"""
    <div style="text-align:center; padding: 4rem 2rem; color:{T['subtext']};">
        <div style="font-size:4rem;">📰</div>
        <div style="font-size:1.3rem; margin-top:1rem;">
            Paste a news URL above and hit <span style="color:{T['accent']}">✨ Analyze</span>
        </div>
        <div style="font-size:0.9rem; margin-top:0.5rem;">
            Works with BBC, Reuters, TechCrunch, Guardian, and more
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:{T['subtext']}; font-size:0.85rem; padding:1rem 0;">
    Built with 🤗 HuggingFace · spaCy · Streamlit · by Abdul Rehman
</div>
""", unsafe_allow_html=True)