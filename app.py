"""
app.py
------
Sentiment-Aware News Summarizer — Gen Z Edition
Themes: Neon Dark, Soft Pastel, Vaporwave, Clean Light, Matcha
Features: Theme picker, one-click copy, article history with auto-analyze,
          word count, reading time, sentiment chart, entity tags,
          responsive: wide on desktop, stacked on mobile
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
    initial_sidebar_state="collapsed"
)

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "🌙 Neon Dark": {
        "bg":       "#0d0d0d",
        "card":     "#1a1a2e",
        "accent":   "#e94560",
        "accent2":  "#0f3460",
        "text":     "#eaeaea",
        "subtext":  "#a0a0b0",
        "positive": "#00ff88",
        "negative": "#ff4466",
        "border":   "#e9456033",
        "tag_bg":   "#e9456022",
        "font":     "Courier New, monospace",
    },
    "🌸 Soft Pastel": {
        "bg":       "#fdf6f0",
        "card":     "#fff8fb",
        "accent":   "#d63a8a",
        "accent2":  "#7c3aed",
        "text":     "#1a1a1a",
        "subtext":  "#444444",
        "positive": "#16a34a",
        "negative": "#dc2626",
        "border":   "#d63a8a33",
        "tag_bg":   "#d63a8a15",
        "font":     "Georgia, serif",
    },
    "🌊 Vaporwave": {
        "bg":       "#1a0533",
        "card":     "#2d0b5e",
        "accent":   "#ff71ce",
        "accent2":  "#01cdfe",
        "text":     "#fffaf0",
        "subtext":  "#c4b5fd",
        "positive": "#05ffa1",
        "negative": "#ff71ce",
        "border":   "#ff71ce33",
        "tag_bg":   "#ff71ce15",
        "font":     "Trebuchet MS, sans-serif",
    },
    "🤍 Clean Light": {
        "bg":       "#f8fafc",
        "card":     "#ffffff",
        "accent":   "#4f46e5",
        "accent2":  "#7c3aed",
        "text":     "#0f172a",
        "subtext":  "#1e293b",
        "positive": "#15803d",
        "negative": "#b91c1c",
        "border":   "#4f46e533",
        "tag_bg":   "#4f46e510",
        "font":     "Inter, sans-serif",
    },
    "🌿 Matcha": {
        "bg":       "#1a1f1a",
        "card":     "#1e2a1e",
        "accent":   "#86efac",
        "accent2":  "#4ade80",
        "text":     "#ecfdf5",
        "subtext":  "#a7f3d0",
        "positive": "#4ade80",
        "negative": "#fca5a5",
        "border":   "#86efac33",
        "tag_bg":   "#86efac15",
        "font":     "monospace",
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

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "theme" not in st.session_state:
    st.session_state.theme = "🌙 Neon Dark"
if "auto_analyze" not in st.session_state:
    st.session_state.auto_analyze = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✨ NewsAI")
    st.markdown("---")

    st.markdown("### 🎨 Pick Your Vibe")
    selected_theme = st.radio(
        label="theme",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme),
        label_visibility="collapsed"
    )
    st.session_state.theme = selected_theme

    st.markdown("---")
    st.markdown("### 🕓 Recent Articles")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            sentiment_icon = "😊" if h["sentiment"] == "Positive" else "😟"
            if st.button(
                f"{sentiment_icon} {h['title'][:30]}...",
                key=f"hist_{i}",
                use_container_width=True
            ):
                st.session_state.prefill_url  = h["url"]
                st.session_state.auto_analyze = True
                st.rerun()
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No articles yet. Analyze something!")

    st.markdown("---")
    st.caption("Built by Abdul Rehman 🚀")

# ── Active theme ──────────────────────────────────────────────────────────────
T = THEMES[st.session_state.theme]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* ── Base ── */
.stApp {{
    background-color: {T['bg']} !important;
    font-family: {T['font']} !important;
}}

/* ── Responsive container ── */
.block-container {{
    max-width: 1200px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    margin: 0 auto !important;
}}
@media (max-width: 768px) {{
    .block-container {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: {T['card']} !important;
    border-right: 1px solid {T['border']} !important;
}}
[data-testid="stSidebar"] * {{
    color: {T['text']} !important;
}}

/* ── Text ── */
.stMarkdown p, .stMarkdown li,
.stMarkdown span, h1, h2, h3, h4 {{
    color: {T['text']} !important;
    font-family: {T['font']} !important;
}}
.stCaption p {{
    color: {T['subtext']} !important;
}}

/* ── Cards ── */
.news-card {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 4px 24px {T['border']};
    color: {T['text']};
}}
.news-card p {{
    color: {T['text']} !important;
}}

/* ── Accent ── */
.accent-text {{
    color: {T['accent']} !important;
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 8px;
}}

/* ── Entity tags ── */
.entity-tag {{
    display: inline-block;
    background: {T['tag_bg']};
    border: 1px solid {T['accent']};
    color: {T['accent']} !important;
    border-radius: 999px;
    padding: 3px 12px;
    margin: 3px;
    font-size: 0.82rem;
    font-weight: 600;
}}

/* ── Stats — 2x2 mobile, 4x1 desktop ── */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin: 16px 0;
}}
@media (min-width: 640px) {{
    .stats-grid {{
        grid-template-columns: repeat(4, 1fr);
    }}
}}
.stat-box {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 14px;
    text-align: center;
}}
.stat-number {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {T['accent']} !important;
}}
.stat-label {{
    font-size: 0.72rem;
    color: {T['subtext']} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}}

/* ── Hero ── */
.hero-title {{
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    background: linear-gradient(135deg, {T['accent']}, {T['accent2']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}}
.hero-sub {{
    color: {T['subtext']} !important;
    font-size: clamp(0.9rem, 2vw, 1.1rem);
    margin-top: 8px;
}}

/* ── Sentiment badges ── */
.sentiment-positive {{
    background: {T['positive']}22;
    color: {T['positive']} !important;
    border: 1px solid {T['positive']};
    border-radius: 999px;
    padding: 6px 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}}
.sentiment-negative {{
    background: {T['negative']}22;
    color: {T['negative']} !important;
    border: 1px solid {T['negative']};
    border-radius: 999px;
    padding: 6px 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}}
.confidence-text {{
    color: {T['subtext']} !important;
    margin-top: 12px;
    font-size: 0.95rem;
}}

/* ── Entity grid — 2x2 mobile, 4x1 desktop ── */
.entity-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin: 16px 0;
}}
@media (min-width: 640px) {{
    .entity-grid {{
        grid-template-columns: repeat(4, 1fr);
    }}
}}
.entity-section {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 14px;
}}
.entity-section-title {{
    color: {T['text']} !important;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 8px;
}}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, {T['accent']}, {T['accent2']}) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 12px !important;
    font-size: 1rem !important;
    transition: opacity 0.2s !important;
}}
.stButton > button:hover {{
    opacity: 0.85 !important;
}}

/* ── Input ── */
.stTextInput > div > div > input {{
    background: {T['card']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    padding: 12px !important;
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: {T['card']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
}}
[data-testid="stExpander"] * {{
    color: {T['text']} !important;
}}

/* ── Divider ── */
hr {{
    border-color: {T['border']} !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: {T['bg']}; }}
::-webkit-scrollbar-thumb {{
    background: {T['accent']};
    border-radius: 3px;
}}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding: 1.5rem 0 1rem 0;">
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
        placeholder="https://www.dawn.com/news/...",
        label_visibility="collapsed"
    )
with col_btn:
    analyze_btn = st.button(
        "✨ Analyze",
        type="primary",
        use_container_width=True
    )

# ── Auto analyze when coming from history ─────────────────────────────────────
if st.session_state.get("auto_analyze") and url:
    analyze_btn = True
    st.session_state.auto_analyze = False

if "prefill_url" in st.session_state:
    del st.session_state.prefill_url

st.markdown("---")

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyze_btn:

    if not url.strip():
        st.warning("⚠️ Paste a URL first bestie!")
        st.stop()
    if not url.startswith(("http://", "https://")):
        st.error("❌ That URL looks sus. Make sure it starts with https://")
        st.stop()

    with st.spinner("🤖 Warming up the AI..."):
        load_all_models()

    with st.spinner("🌐 Fetching article..."):
        try:
            article = scrape_article(url)
        except (ValueError, TypeError) as e:
            st.error(f"❌ Couldn't fetch that article: {e}")
            st.info("💡 Try a direct article URL, not a homepage.")
            st.stop()

    text         = article["text"]
    word_count   = len(text.split())
    reading_time = max(1, round(word_count / 200))

    st.success(f"✅ Got it! **{article['title']}**")

    with st.spinner("🧠 Running AI pipeline..."):
        t0               = time.time()
        summary_result   = summarize(text)
        sentiment_result = analyze_sentiment(text)
        ner_result       = extract_entities(text)
        elapsed          = round(time.time() - t0, 1)

    st.session_state.history.append({
        "url":        url,
        "title":      article["title"],
        "summary":    summary_result["summary"],
        "sentiment":  sentiment_result["label"],
        "confidence": sentiment_result["confidence"],
    })

    # ── Stats ─────────────────────────────────────────────────────────────────
    st.markdown("### 📊 Quick Stats")
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-number">{word_count}</div>
            <div class="stat-label">Words</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{reading_time}m</div>
            <div class="stat-label">Read Time</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{len(ner_result['all_entities'])}</div>
            <div class="stat-label">Entities</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{elapsed}s</div>
            <div class="stat-label">AI Speed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary + Sentiment ───────────────────────────────────────────────────
    summary_text = summary_result["summary"] if summary_result else text
    left, right  = st.columns([3, 2])

    with left:
        st.markdown("### ✍️ AI Summary")
        st.markdown(f"""
        <div class="news-card">
            <div style="display:flex; justify-content:space-between;
                        align-items:center; margin-bottom:12px;">
                <div style="color:{T['accent']}; font-weight:700;
                            font-size:1.05rem;">AI Summary</div>
            </div>
            <p style="line-height:1.8; font-size:1rem; color:{T['text']};">
                {summary_text}
            </p>
            <div style="color:{T['subtext']}; font-size:0.78rem; margin-top:12px;">
                📉 {summary_result['input_chars']} → {summary_result['output_chars']} chars
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Copy button via component ─────────────────────────────────────────
        import streamlit.components.v1 as components
        escaped = summary_text.replace("\\", "\\\\").replace("`", "\\`")
        components.html(f"""
        <button
            id="copybtn"
            onclick="
                var el = document.createElement('textarea');
                el.value = `{escaped}`;
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                document.getElementById('copybtn').innerText = '✅ Copied!';
                document.getElementById('copybtn').style.background = '#22c55e';
                setTimeout(function() {{
                    document.getElementById('copybtn').innerText = '📋 Copy Summary';
                    document.getElementById('copybtn').style.background = 'linear-gradient(135deg, {T['accent']}, {T['accent2']})';
                }}, 2000);
            "
            style="
                background: linear-gradient(135deg, {T['accent']}, {T['accent2']});
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: opacity 0.2s;
                font-family: {T['font']};
            "
            onmouseover="this.style.opacity='0.85'"
            onmouseout="this.style.opacity='1'"
        >📋 Copy Summary</button>
        """, height=55)


    with right:
        st.markdown("### 💬 Sentiment Analysis")
        label       = sentiment_result["label"]
        confidence  = sentiment_result["confidence"]
        pos_score   = sentiment_result["scores"]["Positive"]
        neg_score   = sentiment_result["scores"]["Negative"]
        badge_class = "sentiment-positive" if label == "Positive" else "sentiment-negative"
        emoji       = "😊" if label == "Positive" else "😟"

        st.markdown(f"""
        <div class="news-card" style="text-align:center;">
            <div style="font-size:2.5rem;">{emoji}</div>
            <div class="{badge_class}" style="margin-top:8px;">{label}</div>
            <div class="confidence-text">{confidence*100:.1f}% confident fr fr</div>
        </div>
        """, unsafe_allow_html=True)

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
            margin=dict(t=8, b=8, l=8, r=8),
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

    # ── Named Entities ────────────────────────────────────────────────────────
    st.markdown("### 🏷️ Named Entities")

    def make_tags(items):
        if not items:
            return f'<span style="color:{T["subtext"]}; font-size:0.85rem;">None found</span>'
        return "".join(
            f'<span class="entity-tag">{item}</span>'
            for item in items
        )

    st.markdown(f"""
    <div class="entity-grid">
        <div class="entity-section">
            <div class="entity-section-title">👤 People</div>
            {make_tags(ner_result["people"])}
        </div>
        <div class="entity-section">
            <div class="entity-section-title">🏢 Organizations</div>
            {make_tags(ner_result["organizations"])}
        </div>
        <div class="entity-section">
            <div class="entity-section-title">📍 Locations</div>
            {make_tags(ner_result["locations"])}
        </div>
        <div class="entity-section">
            <div class="entity-section-title">🌍 Groups</div>
            {make_tags(ner_result["groups"])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Expandable sections ───────────────────────────────────────────────────
    with st.expander("📄 Article Metadata"):
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown(f"**🖊️ Authors:** {', '.join(article['authors']) if article['authors'] else 'Not found'}")
            st.markdown(f"**📅 Date:** {article['publish_date'] or 'Not found'}")
            st.markdown(f"**🔧 Method:** {article['method']}")
        with mc2:
            st.markdown(f"**📏 Length:** {len(text)} characters")
            st.markdown(f"**🔗 URL:** {url}")

    with st.expander("📖 Full Article Text"):
        st.markdown(f"""
        <div style="line-height:1.8; color:{T['text']};
                    font-size:0.9rem; padding:8px;">
            {text}
        </div>
        """, unsafe_allow_html=True)

# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown(f"""
    <div style="text-align:center; padding:4rem 1rem;">
        <div style="font-size:4rem;">📰</div>
        <div style="font-size:1.3rem; margin-top:1rem; color:{T['text']};">
            Paste a news URL above and hit
            <span style="color:{T['accent']}; font-weight:700;"> ✨ Analyze</span>
        </div>
        <div style="font-size:0.9rem; margin-top:0.5rem; color:{T['subtext']};">
            Works with BBC, Dawn, Reuters, TechCrunch, Guardian and more
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:{T['subtext']};
            font-size:0.82rem; padding:0.8rem 0;">
    Built with 🤗 HuggingFace · spaCy · Streamlit · by Abdul Rehman
</div>
""", unsafe_allow_html=True)