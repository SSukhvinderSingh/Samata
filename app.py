"""
Samata — AI-Powered Matrimonial Legal Assistant
Streamlit Application Interface.
Features:
- Cinematic Landing Page
- Interactive Floating @mention Autocomplete Tool
- Multi-Agent Deliberation Support
- High-Contrast Theme-Adaptive Palette (Light & Dark Mode Compatible)
- Pure Grounded Citations (Zero internal filenames or raw scores)
"""

import os
import json
import uuid
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

from agents.orchestrator import orchestrate_query
from skills.observability import get_session_traces, clear_session_trace
from skills.feedback_collector import log_feedback
from skills.document_ingestion import parse_file

# Streamlit Page Config
st.set_page_config(
    page_title="Samata — Matrimonial Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend Model Settings
ACTIVE_SLM = os.getenv("OPENROUTER_SLM_MODEL", "meta-llama/llama-3.2-3b-instruct")
ACTIVE_MAIN = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

# Custom CSS — Chambers & Scales of Justice (Theme-Adaptive & High-Prestige)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,400&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Cinematic Hero Container */
    .hero-container {
        text-align: center;
        padding: 40px 20px 20px 20px;
        max-width: 920px;
        margin: 0 auto;
        position: relative;
    }
    .hero-crest {
        width: 68px;
        height: 68px;
        margin: 0 auto 16px auto;
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.2) 0%, rgba(180, 83, 9, 0.05) 100%);
        border: 1.5px solid rgba(217, 119, 6, 0.4);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        box-shadow: 0 4px 20px rgba(217, 119, 6, 0.15);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.76rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #d97706;
        background: rgba(217, 119, 6, 0.10);
        border: 1px solid rgba(217, 119, 6, 0.28);
        padding: 5px 16px;
        border-radius: 24px;
        margin-bottom: 16px;
        font-weight: 700;
    }
    .hero-title {
        font-family: 'Cinzel', serif;
        font-size: 3.8rem;
        font-weight: 900;
        letter-spacing: 0.06em;
        color: var(--text-color);
        margin-bottom: 12px;
        line-height: 1.08;
    }
    .hero-title-accent {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 60%, #b45309 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-tagline {
        font-size: 1.12rem;
        color: var(--text-color);
        opacity: 0.88;
        font-weight: 300;
        max-width: 740px;
        margin: 0 auto 24px auto;
        line-height: 1.65;
    }

    /* Grounding Stats Strip */
    .hero-stats-strip {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 14px;
        margin: 0 auto 30px auto;
        max-width: 820px;
    }
    .stat-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
        font-size: 0.80rem;
        font-weight: 500;
        color: var(--text-color);
    }
    .stat-chip strong {
        color: #d97706;
        font-weight: 700;
    }

    /* 4 Pillars Grid */
    .pillar-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
        gap: 18px;
        margin: 35px auto 25px auto;
        text-align: left;
    }
    .pillar-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 22px 18px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .pillar-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #d97706, transparent);
        opacity: 0.4;
        transition: opacity 0.2s ease;
    }
    .pillar-card:hover {
        border-color: rgba(217, 119, 6, 0.6);
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    }
    .pillar-card:hover::before {
        opacity: 1;
    }
    .pillar-icon-box {
        width: 44px;
        height: 44px;
        border-radius: 10px;
        background: rgba(217, 119, 6, 0.1);
        border: 1px solid rgba(217, 119, 6, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        margin-bottom: 12px;
    }
    .pillar-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--text-color);
        margin-bottom: 6px;
        letter-spacing: -0.01em;
    }
    .pillar-desc {
        font-size: 0.84rem;
        color: var(--text-color);
        opacity: 0.82;
        line-height: 1.55;
    }

    /* Workspace Header */
    .workspace-header {
        font-family: 'Cinzel', serif;
        font-size: 1.95rem;
        font-weight: 800;
        color: var(--text-color);
        letter-spacing: 0.01em;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .workspace-sub {
        font-size: 0.94rem;
        color: var(--text-color);
        opacity: 0.80;
        margin-bottom: 1.2rem;
        line-height: 1.5;
    }

    /* Agent Badges */
    .agent-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 12px;
        letter-spacing: 0.02em;
    }
    .badge-advocate { background: rgba(217, 119, 6, 0.14); color: #d97706; border: 1px solid rgba(217, 119, 6, 0.4); }
    .badge-qa { background: rgba(96, 165, 250, 0.14); color: #3b82f6; border: 1px solid rgba(96, 165, 250, 0.4); }
    .badge-risk { background: rgba(239, 68, 68, 0.14); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-simplify { background: rgba(167, 139, 250, 0.14); color: #8b5cf6; border: 1px solid rgba(167, 139, 250, 0.4); }
    .badge-compare { background: rgba(52, 211, 153, 0.14); color: #10b981; border: 1px solid rgba(52, 211, 153, 0.4); }
    .badge-welcome { background: rgba(13, 148, 136, 0.14); color: #0d9488; border: 1px solid rgba(13, 148, 136, 0.4); }

    /* Interactive Tagging Toolbar */
    .toolbar-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #d97706;
        margin-bottom: 6px;
    }

    /* Section Subtitle */
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-color);
        margin: 18px 0 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "uploaded_doc_text" not in st.session_state:
    st.session_state["uploaded_doc_text"] = None
if "uploaded_doc_chunks" not in st.session_state:
    st.session_state["uploaded_doc_chunks"] = []
if "uploaded_doc_name" not in st.session_state:
    st.session_state["uploaded_doc_name"] = None
if "view" not in st.session_state:
    st.session_state["view"] = "landing"
if "selected_agents" not in st.session_state:
    st.session_state["selected_agents"] = []

# ==============================================================================
# SIDEBAR: ACCESSIBILITY & CHAMBERS NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚖️ **Samata Chambers**")
    st.caption("AI-Powered Matrimonial Legal Intelligence")
    
    st.markdown("---")
    st.markdown("#### ♿ **Accessibility (a11y) Tools**")
    font_size = st.select_slider(
        "Text Sizing",
        options=["Normal", "Large", "Extra Large"],
        value="Normal",
        help="Adjust font sizing across the courtroom interface for enhanced readability (WCAG 2.1 AA)"
    )
    if font_size == "Large":
        st.markdown("<style>html, body, p, [class*='css'], .stMarkdown { font-size: 1.10rem !important; }</style>", unsafe_allow_html=True)
    elif font_size == "Extra Large":
        st.markdown("<style>html, body, p, [class*='css'], .stMarkdown { font-size: 1.22rem !important; }</style>", unsafe_allow_html=True)
    
    high_contrast = st.toggle("High Contrast Focus Rings", value=True, help="Enhances visibility of active controls and keyboard focus")
    if high_contrast:
        st.markdown("<style>button:focus, input:focus, textarea:focus { outline: 3px solid #06b6d4 !important; outline-offset: 2px !important; }</style>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🏛️ **Statutory Coverage**")
    st.markdown("""
    - **HMA 1955**: Hindu Marriage Act
    - **SMA 1954**: Special Marriage Act
    - **DV Act 2005**: Protection of Women
    - **CrPC 125 / BNSS**: Maintenance
    """)

    st.markdown("---")
    st.markdown("#### 🚨 **Emergency Helplines**")
    st.markdown("""
    - **NCW Helpline**: `7827170170`
    - **iCall Distress**: `9152987821`
    - **SNEHI Support**: `011-65978181`
    """)

    st.markdown("---")
    st.caption(f"⚡ **SLM**: `{ACTIVE_SLM.split('/')[-1]}`  \n🧠 **LLM**: `{ACTIVE_MAIN.split('/')[-1]}`")


def get_agent_badge_html(agent_name: str) -> str:
    """Returns a styled theme-adaptive badge HTML for the given agent."""
    if "Devil" in agent_name or "Advocate" in agent_name or "Strategic" in agent_name:
        return '<div class="agent-badge badge-advocate">⚖️ Strategic Multi-Lens Advocate</div>'
    elif "Risk" in agent_name:
        return '<div class="agent-badge badge-risk">🚩 Risk Spotter Agent</div>'
    elif "Simplif" in agent_name:
        return '<div class="agent-badge badge-simplify">🗣️ Plain Language Simplifier</div>'
    elif "Compar" in agent_name:
        return '<div class="agent-badge badge-compare">📊 Legal Comparator</div>'
    elif "Welcome" in agent_name:
        return '<div class="agent-badge badge-welcome">👋 Samata Legal Guide</div>'
    elif "Multi-Agent" in agent_name or "Deliberation" in agent_name:
        return '<div class="agent-badge badge-advocate">🤝 Multi-Agent Deliberation Panel</div>'
    else:
        return '<div class="agent-badge badge-qa">📖 Statutory & Case Law Q&A</div>'


# Per-agent colour palette — matches the dropdown and pill styling
_TAG_META = {
    '@advocate': ('\u2696\ufe0f', '#d97706'),
    '@risk':     ('\U0001f6a9', '#ef4444'),
    '@qa':       ('\U0001f4d6', '#60a5fa'),
    '@simplify': ('\U0001f5e3\ufe0f', '#a78bfa'),
    '@compare':  ('\U0001f4ca', '#34d399'),
}


def highlight_agent_tags(text: str) -> str:
    """Replace @agent mentions with per-agent colored pill spans for rich chat display."""
    import re
    def _pill(m: re.Match) -> str:
        tag = m.group(0).lower()
        icon, color = _TAG_META.get(tag, ('', '#d97706'))
        return (
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:rgba(255,255,255,0.07);color:{color};'
            f'border:1px solid {color};border-radius:6px;'
            f'padding:1px 8px;font-weight:700;font-size:0.85em;'
            f'letter-spacing:0.02em;vertical-align:middle;">'
            f'{icon}\u00a0{m.group(0)}</span>'
        )
    return re.sub(r'@(advocate|risk|qa|simplify|compare)\b', _pill, text, flags=re.IGNORECASE)


# ==============================================================================
# VIEW 1: CINEMATIC NOIR LANDING PAGE
# ==============================================================================
if st.session_state["view"] == "landing":
    st.markdown("""
    <div class="hero-container">
        <div class="hero-crest">⚖️</div>
        <div class="hero-badge">The Matrimonial Legal Intelligence Core</div>
        <div class="hero-title"><span class="hero-title-accent">SAMATA</span></div>
        <div class="hero-tagline">
            Adversarial Precision. Statutory Grounding. Empathetic Clarity.<br>
            Navigate Indian Family Law (Hindu Marriage Act 1955, Special Marriage Act 1954, Divorce Act 1869) through specialist legal agents.
        </div>
        <div class="hero-stats-strip">
            <div class="stat-chip">📚 <strong>13,000+</strong> Chunks Indexed</div>
            <div class="stat-chip">🏛️ <strong>SC</strong> Precedents & Bare Acts</div>
            <div class="stat-chip">⚖️ <strong>5</strong> Specialist Agents</div>
            <div class="stat-chip">🔒 <strong>Zero-Data-Leak</strong> Architecture</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Big Cinematic CTA Button
    col_l, col_m, col_r = st.columns([1, 1.4, 1])
    with col_m:
        if st.button("⚔️ Enter Samata Consultation Chambers →", use_container_width=True, type="primary"):
            st.session_state["view"] = "chat"
            st.rerun()

    # 4 Pillars of Samata
    st.markdown("""
    <div class="pillar-grid">
        <div class="pillar-card">
            <div class="pillar-icon-box">⚖️</div>
            <div class="pillar-title">Strategic Advocate</div>
            <div class="pillar-desc">Stress-test narratives against opposing counsel's counter-claims and the Family Court bench's judicial priorities.</div>
        </div>
        <div class="pillar-card">
            <div class="pillar-icon-box">🚩</div>
            <div class="pillar-title">Risk Spotter</div>
            <div class="pillar-desc">Audit settlement deeds, MOU clauses, and separation drafts for hidden waiver traps and one-sided liabilities.</div>
        </div>
        <div class="pillar-card">
            <div class="pillar-icon-box">📖</div>
            <div class="pillar-title">Grounded Lexicon</div>
            <div class="pillar-desc">Deep retrieval across 13,000+ legal chunks from Supreme Court precedents, Paras Diwan, and statutory bare acts.</div>
        </div>
        <div class="pillar-card">
            <div class="pillar-icon-box">🗣️</div>
            <div class="pillar-title">Vernacular Bridge</div>
            <div class="pillar-desc">Translate dense courtroom legalese into empowering plain English and accessible Hinglish.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### **Samata** ⚖️")
        st.caption("AI-Powered Matrimonial Assistant")
        st.divider()
        if st.button("🚀 Go Directly to Chat", use_container_width=True):
            st.session_state["view"] = "chat"
            st.rerun()


# ==============================================================================
# VIEW 2: INTERACTIVE CONSULTATION WORKSPACE
# ==============================================================================
else:
    with st.sidebar:
        st.markdown("### **Samata Chambers** ⚖️")
        st.caption("Indian Matrimonial & Family Law Assistant")
        
        if st.button("🏛️ Back to Overview (Landing)", use_container_width=True):
            st.session_state["view"] = "landing"
            st.rerun()

        st.divider()
        st.subheader("📄 Case Documents & Deeds (Optional)")
        uploaded_file = st.file_uploader(
            "Attach Draft / Petition / Deed",
            type=["pdf", "docx", "txt"],
            help="Upload mutual consent agreements, notices, or petitions for automated risk analysis."
        )

        if uploaded_file is not None:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            res = parse_file(temp_path)

            # Always clean up the temp file
            try:
                import os as _os
                _os.remove(temp_path)
            except Exception:
                pass

            if res["parse_status"] != "failed":
                doc_chunks = res["chunks"]
                st.session_state["uploaded_doc_text"]   = "\n\n".join([c["chunk_text"] for c in doc_chunks])
                st.session_state["uploaded_doc_chunks"] = doc_chunks   # structured — fed into BM25 retrieval
                st.session_state["uploaded_doc_name"]   = uploaded_file.name
                st.success(f"Attached: {uploaded_file.name} ({len(doc_chunks)} sections parsed)")
                if res["parse_status"] == "ocr_fallback":
                    st.warning(
                        "\u26a0\ufe0f **Scanned / image-only PDF detected.** "
                        "Text extraction was limited — semantic search over this document may be imprecise. "
                        "For best results, upload a text-selectable PDF, DOCX, or TXT version of your deed or petition."
                    )
            else:
                st.error(f"Failed to parse document: {res['error_message']}")


        st.divider()
        st.subheader("🌐 Explanation Style")
        lang_pref = st.radio("Language Mode", ["English", "Hinglish"], index=0)

        st.divider()
        if st.button("Clear Conversation", use_container_width=True):
            clear_session_trace(st.session_state["session_id"])
            st.session_state["session_id"] = str(uuid.uuid4())[:8]
            st.session_state["messages"] = []
            st.session_state["uploaded_doc_text"] = None
            st.session_state["uploaded_doc_chunks"] = []
            st.session_state["uploaded_doc_name"] = None
            st.session_state["selected_agents"] = []
            st.rerun()

        st.caption(f"Session ID: `{st.session_state['session_id']}`")

    # Header
    st.markdown('<div class="workspace-header">Samata Consultation Chambers ⚖️</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="workspace-sub">Ask questions, evaluate dispute scenarios, or tag multiple specialists (e.g. <code>@risk @advocate</code>) for collaborative cross-examination.</div>',
        unsafe_allow_html=True
    )

    # Interactive Specialist Agent Multi-Tagging Toolbar
    st.markdown("**Tag Specialists (Click to add to your consultation):**")
    tag_cols = st.columns(6)
    
    with tag_cols[0]:
        if st.button("⚖️ @advocate", use_container_width=True):
            if "@advocate" not in st.session_state["selected_agents"]:
                st.session_state["selected_agents"].append("@advocate")
            st.rerun()
    with tag_cols[1]:
        if st.button("🚩 @risk", use_container_width=True):
            if "@risk" not in st.session_state["selected_agents"]:
                st.session_state["selected_agents"].append("@risk")
            st.rerun()
    with tag_cols[2]:
        if st.button("🗣️ @simplify", use_container_width=True):
            if "@simplify" not in st.session_state["selected_agents"]:
                st.session_state["selected_agents"].append("@simplify")
            st.rerun()
    with tag_cols[3]:
        if st.button("📊 @compare", use_container_width=True):
            if "@compare" not in st.session_state["selected_agents"]:
                st.session_state["selected_agents"].append("@compare")
            st.rerun()
    with tag_cols[4]:
        if st.button("📖 @qa", use_container_width=True):
            if "@qa" not in st.session_state["selected_agents"]:
                st.session_state["selected_agents"].append("@qa")
            st.rerun()
    with tag_cols[5]:
        if st.button("🔄 Clear Tags", use_container_width=True):
            st.session_state["selected_agents"] = []
            st.rerun()

    # Active tag status pill
    selected = st.session_state.get("selected_agents", [])
    if selected:
        tag_str = " ".join(selected)
        st.info(f"🎯 **Active Multi-Agent Panel**: `{tag_str}` *(All tagged agents will collaborate on your query)*")

    # Dynamic Chat Input Border Theme CSS (Python-rendered for instant toolbar sync)
    AGENT_BORDER_COLORS = {
        "@advocate": "#d97706",
        "@risk": "#ef4444",
        "@qa": "#60a5fa",
        "@simplify": "#a78bfa",
        "@compare": "#34d399",
    }
    MULTI_AGENT_BORDER_COLOR = "#06b6d4"

    if selected:
        active_border_color = AGENT_BORDER_COLORS.get(selected[0], "#d97706") if len(selected) == 1 else MULTI_AGENT_BORDER_COLOR
        st.markdown(f"""
        <style>
            div[data-testid="stChatInput"],
            div[data-testid="stChatInput"] [data-baseweb="base-input"],
            div[data-testid="stChatInput"] [data-baseweb="textarea"],
            div[data-testid="stChatInput"] > div,
            div[data-testid="stChatFloatingInputContainer"] [data-baseweb="base-input"] {{
                border-color: {active_border_color} !important;
                box-shadow: 0 0 0 1.5px {active_border_color}, 0 0 12px {active_border_color}40 !important;
                outline: none !important;
            }}
            div[data-testid="stChatInput"] textarea {{
                outline: none !important;
                box-shadow: none !important;
            }}
            div[data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"] svg,
            div[data-testid="stChatInput"] button svg {{
                fill: {active_border_color} !important;
                color: {active_border_color} !important;
            }}
        </style>
        """, unsafe_allow_html=True)

    if st.session_state["uploaded_doc_name"]:
        st.info(f"📋 **Active Document Context**: `{st.session_state['uploaded_doc_name']}`")

    # @mention autocomplete & dynamic border theme — injected via components.html
    import streamlit.components.v1 as components
    server_selected_json = json.dumps(selected)
    js_template = """<!DOCTYPE html><html><body><script>
(function(){
    // Per-iframe instance token: new on every Streamlit rerun, so stale _samata flags are ignored
    var INST = 'si_' + Math.random().toString(36).substr(2,9);
    var SERVER_SELECTED = %s;
    var AGENTS = [
        {tag:'@advocate', color:'#d97706', desc:'Stress-test your position'},
        {tag:'@risk',     color:'#ef4444', desc:'Audit clauses and deeds'},
        {tag:'@qa',       color:'#60a5fa', desc:'Statutory and case law'},
        {tag:'@simplify', color:'#a78bfa', desc:'Plain English / Hinglish'},
        {tag:'@compare',  color:'#34d399', desc:'Clause vs baseline'}
    ];
    var drop=null, atStart=-1, ta=null, activeIdx=0;

    function getDoc(){ return window.parent.document; }
    function items(){ return drop ? Array.from(drop.querySelectorAll('[data-tag]')) : []; }

    function setActive(idx){
        activeIdx = Math.max(0, Math.min(idx, AGENTS.length-1));
        items().forEach(function(el, i){
            var ag = AGENTS[i];
            if(i === activeIdx){
                el.style.background  = 'rgba(255,255,255,0.07)';
                el.style.borderLeft  = '3px solid '+ag.color;
                el.style.paddingLeft = '11px';
                el.querySelector('.at-tag').style.color  = ag.color;
                el.querySelector('.at-desc').style.color = '#e5e0d0';
            } else {
                el.style.background  = '';
                el.style.borderLeft  = '3px solid transparent';
                el.style.paddingLeft = '11px';
                el.querySelector('.at-tag').style.color  = ag.color;
                el.querySelector('.at-desc').style.color = '#9ca3af';
            }
        });
    }

    function mkDropdown(){
        var d = getDoc();
        var ex = d.getElementById('samata-dd');
        if(ex){ drop=ex; return; }
        drop = d.createElement('div');
        drop.id = 'samata-dd';
        drop.style.cssText = 'position:fixed;display:none;z-index:2147483647;min-width:260px;'
            +'background:#0f0c1c;border-radius:10px;padding:6px 0;'
            +'box-shadow:0 -8px 32px rgba(0,0,0,0.75);font-family:Inter,system-ui,sans-serif;';
        var hdr = d.createElement('div');
        hdr.style.cssText = 'font-size:10px;letter-spacing:.12em;text-transform:uppercase;'
            +'color:#d97706;padding:6px 14px 4px;font-weight:700;'
            +'border-bottom:1px solid rgba(217,119,6,.25);margin-bottom:4px;';
        hdr.textContent = 'Tag a Specialist';
        drop.appendChild(hdr);
        AGENTS.forEach(function(ag, i){
            var el = d.createElement('div');
            el.dataset.tag = ag.tag;
            el.style.cssText = 'display:flex;align-items:center;gap:10px;padding:9px 11px 9px 14px;'
                +'cursor:pointer;font-size:13px;border-left:3px solid transparent;';
            var ts = d.createElement('span'); ts.className='at-tag';
            ts.style.cssText = 'font-weight:700;min-width:90px;color:'+ag.color+';';
            ts.textContent = ag.tag;
            var ds = d.createElement('span'); ds.className='at-desc';
            ds.style.cssText = 'font-size:11px;color:#9ca3af;';
            ds.textContent = ag.desc;
            el.appendChild(ts); el.appendChild(ds);
            el.onmouseenter = function(){ setActive(i); };
            el.onmousedown  = function(e){ e.preventDefault(); insertTag(ag.tag); };
            drop.appendChild(el);
        });
        d.body.appendChild(drop);
    }

    function positionDrop(){
        if(!ta||!drop) return;
        var r = ta.getBoundingClientRect();
        drop.style.display = 'block';
        requestAnimationFrame(function(){
            drop.style.left = r.left + 'px';
            drop.style.top  = (r.top - drop.offsetHeight - 10) + 'px';
        });
    }

    function hideDrop(){
        if(drop) drop.style.display = 'none';
        atStart = -1;
    }

    var MULTI_AGENT_COLOR = '#06b6d4'; // Distinct Electric Cyan for Multi-Agent Collaboration

    function applyBorderTheme(color){
        var d = getDoc();
        var styleEl = d.getElementById('samata-chat-border');
        if(!styleEl){
            styleEl = d.createElement('style');
            styleEl.id = 'samata-chat-border';
            d.head.appendChild(styleEl);
        }
        if(!color){
            styleEl.textContent = '';
            if(ta){
                var c1 = ta.closest('[data-testid="stChatInput"]');
                if(c1){ c1.style.borderColor = ''; c1.style.boxShadow = ''; }
                var c2 = ta.closest('[data-baseweb="base-input"]');
                if(c2){ c2.style.borderColor = ''; c2.style.boxShadow = ''; }
            }
            return;
        }

        styleEl.textContent =
            'div[data-testid="stChatInput"], ' +
            'div[data-testid="stChatInput"] [data-baseweb="base-input"], ' +
            'div[data-testid="stChatInput"] [data-baseweb="textarea"], ' +
            'div[data-testid="stChatInput"] > div, ' +
            'div[data-testid="stChatFloatingInputContainer"] [data-baseweb="base-input"] {' +
            '  border-color: ' + color + ' !important;' +
            '  box-shadow: 0 0 0 1.5px ' + color + ', 0 0 10px ' + color + '40 !important;' +
            '  outline: none !important;' +
            '} ' +
            'div[data-testid="stChatInput"] textarea {' +
            '  outline: none !important;' +
            '  box-shadow: none !important;' +
            '} ' +
            'div[data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"] svg, ' +
            'div[data-testid="stChatInput"] button svg {' +
            '  fill: ' + color + ' !important;' +
            '  color: ' + color + ' !important;' +
            '}';

        if(ta){
            var el1 = ta.closest('[data-testid="stChatInput"]');
            if(el1){
                el1.style.setProperty('border-color', color, 'important');
                el1.style.setProperty('box-shadow', '0 0 0 1.5px ' + color + ', 0 0 10px ' + color + '40', 'important');
            }
            var el2 = ta.closest('[data-baseweb="base-input"]');
            if(el2){
                el2.style.setProperty('border-color', color, 'important');
                el2.style.setProperty('box-shadow', '0 0 0 1.5px ' + color + ', 0 0 10px ' + color + '40', 'important');
            }
        }
    }

    function updateGlow(){
        if(!ta) return;
        var val = ta.value || '';
        var tagged = AGENTS.filter(function(ag){
            return new RegExp(ag.tag+'\\b','i').test(val);
        });

        if(tagged.length === 0){
            if(SERVER_SELECTED && SERVER_SELECTED.length > 0){
                if(SERVER_SELECTED.length === 1){
                    var match = AGENTS.find(function(ag){ return ag.tag === SERVER_SELECTED[0]; });
                    applyBorderTheme(match ? match.color : '#d97706');
                } else {
                    applyBorderTheme(MULTI_AGENT_COLOR);
                }
            } else {
                applyBorderTheme(null);
            }
        } else if(tagged.length === 1){
            applyBorderTheme(tagged[0].color);
        } else {
            // Distinct multi-agent border color
            applyBorderTheme(MULTI_AGENT_COLOR);
        }
    }

    function insertTag(tag){
        if(!ta) return;
        var before = ta.value.substring(0, atStart);
        var after  = ta.value.substring(ta.selectionStart);
        var nv = before + tag + ' ' + after;
        var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
        setter.call(ta, nv);
        ta.dispatchEvent(new Event('input',{bubbles:true}));
        var p = before.length + tag.length + 1;
        ta.setSelectionRange(p, p); ta.focus(); hideDrop(); updateGlow();
    }

    function setupTA(textarea){
        if(textarea._samataInst === INST) return;  // already wired by THIS iframe instance
        textarea._samataInst = INST;
        ta = textarea;
        textarea.addEventListener('input', function(){
            var val=textarea.value, pos=textarea.selectionStart;
            var seg=val.substring(0,pos), idx=seg.lastIndexOf('@');
            if(idx!==-1 && !/\\s/.test(seg.substring(idx+1))){
                atStart=idx; mkDropdown(); activeIdx=0; setActive(0); positionDrop();
            } else { hideDrop(); }
            try{ updateGlow(); }catch(e){}
        });
        textarea.addEventListener('keyup',  function(){ try{updateGlow();}catch(e){} });
        textarea.addEventListener('blur',   function(){ setTimeout(hideDrop,160); try{updateGlow();}catch(e){} });
        textarea.addEventListener('focus',  function(){ try{updateGlow();}catch(e){} });
        textarea.addEventListener('keydown', function(e){
            if(!drop||drop.style.display==='none') return;
            if(e.key==='ArrowDown'){
                e.preventDefault(); e.stopPropagation(); setActive(activeIdx+1);
            } else if(e.key==='ArrowUp'){
                e.preventDefault(); e.stopPropagation(); setActive(activeIdx-1);
            } else if(e.key==='Enter'||e.key==='Tab'){
                e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
                var all=items(); if(all[activeIdx]) insertTag(all[activeIdx].dataset.tag);
            } else if(e.key==='Escape'){
                e.preventDefault(); e.stopPropagation(); hideDrop();
            }
        }, true);
        try{ updateGlow(); }catch(e){}
    }

    function findTA(){
        try{ getDoc().querySelectorAll('textarea').forEach(function(t){ setupTA(t); }); }catch(e){}
    }
    findTA();
    try{ new MutationObserver(findTA).observe(getDoc().body,{childList:true,subtree:true}); }catch(e){}
})();
    </script></body></html>"""
    components.html(js_template % server_selected_json, height=0)



    # Quick Starter Cards (if empty chat)
    if not st.session_state["messages"]:
        st.markdown('<div class="section-title">⚖️ Case Evaluation & Consultation Starters</div>', unsafe_allow_html=True)
        st.caption("Select a scenario or type your specific dispute question below to begin your deliberation:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚖️ Strategy: Stress-test narrative against opposing claims", use_container_width=True):
                st.session_state["prefill"] = "@advocate My spouse left our matrimonial home 6 months ago without explanation and is now seeking interim maintenance."
                st.rerun()
            if st.button("📖 Statutory Law: Interim maintenance standards under Section 24", use_container_width=True):
                st.session_state["prefill"] = "What factors does the court consider when awarding interim maintenance under Section 24 of the Hindu Marriage Act?"
                st.rerun()
        with col2:
            if st.button("🚩 Risk Audit: Check waiver clauses in mutual consent draft", use_container_width=True):
                st.session_state["prefill"] = "@risk Party A unconditionally waives all past, present, and future claims to permanent alimony or maintenance."
                st.rerun()
            if st.button("🤝 Joint Cross-Examination: Risk Spotter + Strategic Advocate", use_container_width=True):
                st.session_state["prefill"] = "@risk @advocate The draft deed states that I forfeit all custody rights and property claims upon signing."
                st.rerun()

    # Render Chat Messages
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                agent_name = "Q&A Agent"
                if "agent_trace" in msg and msg["agent_trace"]:
                    invoked = msg["agent_trace"].get("agents_invoked", [])
                    if len(invoked) > 1:
                        agent_name = "Multi-Agent Deliberation Panel"
                    elif invoked:
                        agent_name = invoked[0]
                
                st.markdown(get_agent_badge_html(agent_name), unsafe_allow_html=True)
                st.markdown(msg["content"])
                
                # Non-intrusive collapsible legal citation & source trace (Zero file names)
                if "agent_trace" in msg and msg["agent_trace"]:
                    trace = msg["agent_trace"]
                    with st.expander("🔍 Legal Verification & Grounding"):
                        invoked_display = [a.replace("Devil's Advocate", "Strategic Advocate") for a in trace.get('agents_invoked', [agent_name])]
                        st.caption(f"**Specialist Agents Invoked**: `{', '.join(invoked_display)}`")
                        traces = get_session_traces(st.session_state["session_id"])
                        if traces and traces[-1].get("retrieved_chunks"):
                            st.markdown("**Statutory & Precedent Citations**:")
                            seen_headings = set()
                            for idx, chunk in enumerate(traces[-1]["retrieved_chunks"][:3]):
                                heading = chunk.get("section_heading", "Statutory Provision")
                                if heading and heading not in seen_headings:
                                    seen_headings.add(heading)
                                    st.markdown(f"- **{heading}**")

                # Thumbs Feedback
                if "response_id" in msg:
                    col1, col2, _ = st.columns([0.8, 0.8, 8.4])
                    with col1:
                        if st.button("👍", key=f"up_{msg['response_id']}"):
                            log_feedback(st.session_state["session_id"], "Orchestrator", msg["response_id"], "thumbs_up")
                            st.toast("Thank you for your feedback!")
                    with col2:
                        if st.button("👎", key=f"down_{msg['response_id']}"):
                            log_feedback(st.session_state["session_id"], "Orchestrator", msg["response_id"], "thumbs_down")
                            st.toast("Feedback recorded.")
            else:
                # Render user message — @tags displayed as styled pills
                st.markdown(highlight_agent_tags(msg["content"]), unsafe_allow_html=True)


    prefill_val = st.session_state.pop("prefill", None)
    selected = st.session_state.get("selected_agents", [])
    tag_prefix = " ".join(selected) + " " if selected else ""

    user_input = st.chat_input("Type @ to tag a specialist, or ask your legal question...")
    effective_input = (tag_prefix + prefill_val).strip() if prefill_val else user_input

    if effective_input:
        if selected:
            for t in selected:
                if t not in effective_input:
                    effective_input = f"{t} {effective_input}"

        # Persist user turn
        st.session_state["messages"].append({"role": "user", "content": effective_input})

        # Render user message immediately so it is visible above the spinner
        with st.chat_message("user"):
            st.markdown(highlight_agent_tags(effective_input), unsafe_allow_html=True)

        # Render assistant thinking indicator inside assistant bubble
        with st.chat_message("assistant"):
            with st.spinner("Analyzing legal principles & preparing grounded response..."):
                lang_code = "hinglish" if lang_pref == "Hinglish" else "en"
                response_dict = orchestrate_query(
                    user_message=effective_input,
                    session_id=st.session_state["session_id"],
                    document_text=st.session_state["uploaded_doc_text"],
                    document_chunks=st.session_state.get("uploaded_doc_chunks", []),
                    user_language_preference=lang_code,
                    slm_model=ACTIVE_SLM,
                    main_model=ACTIVE_MAIN,
                    chat_history=st.session_state["messages"][:-1]
                )

        response_text = response_dict["response"]
        trace_data = response_dict["agent_trace"]
        response_id = f"resp_{len(st.session_state['messages'])}"

        # Reset tags, persist assistant turn, then rerun — history loop renders everything
        st.session_state["selected_agents"] = []
        st.session_state["messages"].append({
            "role": "assistant",
            "content": response_text,
            "agent_trace": trace_data,
            "response_id": response_id
        })
        st.rerun()


