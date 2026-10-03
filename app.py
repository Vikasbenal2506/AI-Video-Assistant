import html
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain

load_dotenv()

st.set_page_config(page_title="AI Video Assistant", page_icon="🎬", layout="wide")

# ---------------------------------------------------------------- Themes
THEMES = {
    "Midnight": dict(
        bg="#0b1020", bg2="#121936", surface="#161e3f", text="#e8ecff", muted="#8f9ac4",
        border="rgba(143,154,196,.22)", a1="#7c5cff", a2="#22d3ee", btn_text="#ffffff",
        hero="linear-gradient(120deg,#3b2bb5 0%,#7c5cff 45%,#22d3ee 100%)", hero_text="#ffffff",
    ),
    "Daylight": dict(
        bg="#f6f7fb", bg2="#ffffff", surface="#ffffff", text="#1b1f3b", muted="#6a7094",
        border="rgba(27,31,59,.12)", a1="#4f46e5", a2="#ec4899", btn_text="#ffffff",
        hero="linear-gradient(120deg,#4f46e5 0%,#8b5cf6 50%,#ec4899 100%)", hero_text="#ffffff",
    ),
    "Sunset": dict(
        bg="#1a0f1f", bg2="#25142b", surface="#2c1833", text="#fff0e8", muted="#c39bb0",
        border="rgba(255,176,140,.22)", a1="#ff7a45", a2="#ff4d8d", btn_text="#ffffff",
        hero="linear-gradient(120deg,#ff4d8d 0%,#ff7a45 55%,#ffc145 100%)", hero_text="#2a0f1c",
    ),
}


def inject_css(t: dict):
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root {{
  --bg:{t['bg']}; --bg2:{t['bg2']}; --surface:{t['surface']}; --text:{t['text']};
  --muted:{t['muted']}; --border:{t['border']}; --a1:{t['a1']}; --a2:{t['a2']};
}}
html, body, .stApp, [class*="css"] {{ font-family:'Plus Jakarta Sans',sans-serif; }}
.stApp {{ background: radial-gradient(1200px 600px at 85% -10%, {t['a1']}22, transparent 60%),
          radial-gradient(900px 500px at -10% 110%, {t['a2']}1f, transparent 60%), var(--bg); color:var(--text); }}
header[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:1.5rem; max-width:1150px; }}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp div[data-testid="stMarkdownContainer"] {{ color:var(--text); }}
.stApp [data-testid="stCaptionContainer"], .stApp small {{ color:var(--muted); }}

/* Sidebar */
section[data-testid="stSidebar"] {{ background:var(--bg2); border-right:1px solid var(--border); }}
.brand {{ display:flex; align-items:center; gap:.7rem; margin-bottom:.4rem; }}
.brand .logo {{ width:42px; height:42px; border-radius:12px; display:grid; place-items:center;
  font-size:1.35rem; background:linear-gradient(135deg,var(--a1),var(--a2)); }}
.brand .name {{ font-weight:800; font-size:1.15rem; line-height:1.1; }}
.brand .tag {{ color:var(--muted); font-size:.78rem; }}

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {{
  background:var(--surface)!important; color:var(--text)!important;
  border:1px solid var(--border)!important; border-radius:12px!important; }}
[data-testid="stFileUploaderDropzone"] {{ background:var(--surface); border:1.5px dashed var(--a1); border-radius:14px; }}
[data-testid="stFileUploaderDropzone"] * {{ color:var(--text)!important; }}

/* Buttons */
.stButton > button, .stDownloadButton > button {{
  border-radius:12px; font-weight:700; border:1px solid var(--border);
  background:var(--surface); color:var(--text); padding:.6rem 1rem; transition:all .15s ease; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:var(--a1); transform:translateY(-1px); }}
.stButton > button[kind="primary"] {{
  background:linear-gradient(135deg,var(--a1),var(--a2)); color:{t['btn_text']}; border:none;
  box-shadow:0 8px 24px -8px var(--a1); }}
.stButton > button[kind="primary"]:disabled {{ opacity:.45; box-shadow:none; }}

/* Hero */
.hero {{ background:{t['hero']}; color:{t['hero_text']}; border-radius:24px; padding:2.4rem 2.6rem;
  position:relative; overflow:hidden; margin-bottom:1.6rem; }}
.hero::after {{ content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px;
  border-radius:50%; background:rgba(255,255,255,.14); }}
.hero::before {{ content:""; position:absolute; right:110px; bottom:-90px; width:200px; height:200px;
  border-radius:50%; background:rgba(255,255,255,.10); }}
.hero h1, .hero p, .hero span {{ color:{t['hero_text']}!important; position:relative; z-index:1; }}
.hero h1 {{ font-size:2.5rem; font-weight:800; margin:0 0 .5rem 0; letter-spacing:-.02em; }}
.hero p {{ font-size:1.05rem; max-width:560px; opacity:.92; margin:0; }}
.chips {{ margin-top:1.2rem; display:flex; gap:.5rem; flex-wrap:wrap; position:relative; z-index:1; }}
.chip {{ background:rgba(255,255,255,.2); backdrop-filter:blur(6px); padding:.35rem .8rem;
  border-radius:999px; font-size:.82rem; font-weight:600; }}

/* Cards */
.card {{ background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:1.3rem 1.4rem; height:100%; }}
.card .icon {{ width:44px; height:44px; border-radius:12px; display:grid; place-items:center; font-size:1.3rem;
  background:linear-gradient(135deg,var(--a1)33,var(--a2)33); margin-bottom:.8rem; }}
.card h4 {{ margin:0 0 .3rem 0; font-size:1.02rem; font-weight:700; }}
.card p {{ margin:0; color:var(--muted)!important; font-size:.9rem; line-height:1.5; }}

/* Result header + stats */
.result-head {{ background:{t['hero']}; border-radius:22px; padding:1.6rem 2rem; margin-bottom:1.2rem; }}
.result-head .label {{ color:{t['hero_text']}; opacity:.85; font-size:.82rem; font-weight:600; }}
.result-head .title {{ color:{t['hero_text']}; font-size:1.9rem; font-weight:800; letter-spacing:-.02em; margin-top:.2rem; }}
.stat {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:1rem 1.2rem; }}
.stat .v {{ font-size:1.6rem; font-weight:800;
  background:linear-gradient(135deg,var(--a1),var(--a2)); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; }}
.stat .k {{ color:var(--muted); font-size:.82rem; font-weight:600; }}

/* Tabs as pills */
.stTabs [data-baseweb="tab-list"] {{ gap:.4rem; border-bottom:none; flex-wrap:wrap; margin-top:.6rem; }}
.stTabs [data-baseweb="tab"] {{ background:var(--surface); border:1px solid var(--border);
  border-radius:999px; padding:.45rem 1.1rem; font-weight:600; height:auto; }}
.stTabs [aria-selected="true"] {{ background:linear-gradient(135deg,var(--a1),var(--a2)); border-color:transparent; }}
.stTabs [aria-selected="true"] p {{ color:#fff!important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}
.panel {{ background:var(--surface); border:1px solid var(--border); border-radius:18px;
  padding:1.4rem 1.6rem; margin-top:.8rem; line-height:1.65; }}

/* Chat */
[data-testid="stChatMessage"] {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; }}
[data-testid="stChatInput"] {{ border-radius:14px; }}
[data-testid="stStatusWidget"], [data-testid="stExpander"], div[data-testid="stStatus"] {{
  background:var(--surface); border:1px solid var(--border); border-radius:14px; }}
hr {{ border-color:var(--border); }}
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- State
DEFAULTS = {"result": None, "messages": [], "source_label": "", "language": "english"}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def build_report(r: dict) -> str:
    return (
        f"# {r['title']}\n\n## Summary\n{r['summary']}\n\n"
        f"## Action items\n{r['action_items']}\n\n"
        f"## Key decisions\n{r['key_decisions']}\n\n"
        f"## Open questions\n{r['open_questions']}\n\n"
        f"## Full transcript\n{r['transcript']}\n"
    )


def run_pipeline(source: str, language: str) -> dict:
    with st.status("Analyzing your video...", expanded=True) as status:
        st.write("🎧 Downloading and preparing audio")
        chunks = process_input(source)
        st.write("📝 Transcribing speech")
        transcript = transcribe_all(chunks, language)
        st.write("✨ Writing title and summary")
        title = generate_title(transcript)
        summary = summarize(transcript)
        st.write("✅ Extracting action items, decisions and open questions")
        actions = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)
        st.write("🔎 Indexing transcript for chat")
        rag_chain = build_rag_chain(transcript)
        status.update(label="Analysis complete", state="complete", expanded=False)
    return {
        "title": title.strip().strip('"'),
        "transcript": transcript,
        "summary": summary,
        "action_items": actions,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    theme_name = st.selectbox("Design", list(THEMES), index=0)
    inject_css(THEMES[theme_name])

    st.markdown(
        "<div class='brand'><div class='logo'>🎬</div><div>"
        "<div class='name'>AI Video Assistant</div>"
        "<div class='tag'>Notes, answers, action items</div></div></div>",
        unsafe_allow_html=True,
    )
    st.divider()

    input_type = st.radio("Source", ["YouTube URL", "Upload file"], horizontal=True)
    youtube_url, uploaded = "", None
    if input_type == "YouTube URL":
        youtube_url = st.text_input("YouTube link", placeholder="https://www.youtube.com/watch?v=...")
    else:
        uploaded = st.file_uploader(
            "Audio or video file", type=["mp3", "wav", "m4a", "mp4", "mkv", "mov", "webm"]
        )
    language = st.selectbox("Spoken language", ["english", "hinglish"])

    can_run = bool(youtube_url.strip()) if input_type == "YouTube URL" else uploaded is not None
    analyze = st.button("Analyze video", type="primary", use_container_width=True, disabled=not can_run)

    if st.session_state.result:
        st.button("Start over", on_click=reset, use_container_width=True)

    if not os.getenv("MISTRAL_API_KEY") and not os.getenv("GROQ_API_KEY"):
        st.warning("No API key found. Add it to your .env file.")

# ---------------------------------------------------------------- Run
if analyze:
    st.session_state.messages = []
    try:
        if input_type == "YouTube URL":
            source = youtube_url.strip()
            st.session_state.source_label = source
        else:
            suffix = os.path.splitext(uploaded.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getbuffer())
                source = tmp.name
            st.session_state.source_label = uploaded.name
        st.session_state.language = language
        st.session_state.result = run_pipeline(source, language)
    except Exception as exc:
        st.session_state.result = None
        st.error(
            f"Processing failed: {exc}\n\n"
            "If the message mentions ffmpeg, install it and restart your terminal."
        )

result = st.session_state.result

# ---------------------------------------------------------------- Empty state
if not result:
    st.markdown(
        """
<div class="hero">
  <h1>Turn any video into<br>clear, searchable notes</h1>
  <p>Paste a YouTube link or upload a recording. Get a summary, action items and decisions,
  then ask questions about what was said.</p>
  <div class="chips"><span class="chip">YouTube links</span><span class="chip">Local audio and video</span>
  <span class="chip">English and Hinglish</span><span class="chip">Chat with the transcript</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
    cards = [
        ("🔗", "Add a source", "Use the sidebar to paste a YouTube link or upload a file."),
        ("🧠", "Get the notes", "Title, summary, action items, key decisions and open questions."),
        ("💬", "Ask anything", "Chat with the transcript. Answers come only from what was said."),
    ]
    cols = st.columns(3)
    for col, (icon, head, body) in zip(cols, cards):
        col.markdown(
            f"<div class='card'><div class='icon'>{icon}</div><h4>{head}</h4><p>{body}</p></div>",
            unsafe_allow_html=True,
        )
    st.stop()

# ---------------------------------------------------------------- Results
st.markdown(
    f"<div class='result-head'><div class='label'>{html.escape(st.session_state.source_label)}</div>"
    f"<div class='title'>{html.escape(result['title'])}</div></div>",
    unsafe_allow_html=True,
)

words = len(result["transcript"].split())
stats = [
    (f"{words:,}", "Words transcribed"),
    (f"~{max(1, round(words / 200))} min", "Reading time"),
    (st.session_state.language.capitalize(), "Language"),
]
for col, (val, key) in zip(st.columns(3), stats):
    col.markdown(f"<div class='stat'><div class='v'>{val}</div><div class='k'>{key}</div></div>", unsafe_allow_html=True)

st.write("")
st.download_button("⬇ Download report (.md)", build_report(result), "meeting_report.md", "text/markdown")

tabs = st.tabs(["📋 Summary", "✅ Action items", "🔑 Decisions", "❓ Open questions", "📝 Transcript", "💬 Chat"])

for tab, key in zip(tabs[:4], ["summary", "action_items", "key_decisions", "open_questions"]):
    with tab:
        with st.container(border=True):
            st.markdown(result[key])

with tabs[4]:
    query = st.text_input("Search transcript", placeholder="Type a word or phrase", label_visibility="collapsed")
    text = result["transcript"]
    if query:
        hits = [s.strip() for s in text.split(". ") if query.lower() in s.lower()]
        st.caption(f"{len(hits)} matching sentence(s)")
        with st.container(border=True):
            for s in hits:
                st.markdown(f"- {s}.")
    else:
        st.text_area("Transcript", text, height=450, label_visibility="collapsed")

with tabs[5]:
    st.caption("Answers come only from this video's transcript.")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask something about the video"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Searching the transcript..."):
                try:
                    answer = result["rag_chain"].invoke(prompt)
                except Exception as exc:
                    answer = f"Something went wrong while answering: {exc}"
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})