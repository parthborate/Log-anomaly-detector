import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from dotenv import load_dotenv
from parser import parse_hdfs_logs
from features import engineer_features
from detector import detect_anomalies
from explainer import setup_llm, explain_anomaly, get_context_window

load_dotenv()

# ──────────────────────────────────────────────
# PAGE CONFIG & CUSTOM CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Log Anomaly Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* ── Import fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

    /* ── Global ── */
    .stApp {
        background: #0a0e17;
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0d1220 !important;
        border-right: 1px solid #1a2332;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: #8892a4 !important;
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Header area ── */
    .main-header {
        padding: 2rem 0 1rem 0;
        border-bottom: 1px solid #1a2332;
        margin-bottom: 2rem;
    }
    .main-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #e2e8f0;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .main-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
        color: #4a5568;
        margin-top: 0.4rem;
    }
    .main-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #fff;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-left: 0.8rem;
        vertical-align: middle;
    }

    /* ── Metric cards ── */
    .metric-row {
        display: flex;
        gap: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        flex: 1;
        background: linear-gradient(145deg, #111827 0%, #0d1220 100%);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        transition: border-color 0.2s;
    }
    .metric-card:hover {
        border-color: #334155;
    }
    .metric-card.anomaly {
        border-color: #ef4444;
        border-width: 1px;
    }
    .metric-card.rate {
        border-color: #f59e0b;
        border-width: 1px;
    }
    .metric-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1;
    }
    .metric-value.red { color: #ef4444; }
    .metric-value.amber { color: #f59e0b; }
    .metric-value.green { color: #10b981; }
    .metric-detail {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.78rem;
        color: #475569;
        margin-top: 0.5rem;
    }

    /* ── Section headers ── */
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 600;
        color: #cbd5e1;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid #1e293b;
        margin: 2rem 0 1.2rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .section-dot.red { background: #ef4444; }
    .section-dot.blue { background: #3b82f6; }
    .section-dot.purple { background: #8b5cf6; }
    .section-dot.green { background: #10b981; }

    /* ── Anomaly table styling ── */
    .stDataFrame {
        border: 1px solid #1e293b;
        border-radius: 8px;
        overflow: hidden;
    }

    /* ── Expander (AI explanations) ── */
    .streamlit-expanderHeader {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
    }
    .streamlit-expanderContent {
        background: #0d1220 !important;
        border: 1px solid #1e293b !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        font-family: 'DM Sans', sans-serif;
        color: #cbd5e1;
        line-height: 1.7;
    }

    /* ── Sidebar styling ── */
    .sidebar-brand {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #10b981;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #1a2332;
    }
    .sidebar-section {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 1.5rem 0 0.6rem 0;
    }
    .sidebar-info {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #334155;
        background: #0a0e17;
        border: 1px solid #1a2332;
        border-radius: 6px;
        padding: 0.8rem;
        margin-top: 1rem;
        line-height: 1.6;
    }

    /* ── Hide default Streamlit elements ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Fix default text colors ── */
    .stMarkdown, .stMarkdown p {
        color: #cbd5e1;
    }

    /* ── Plotly chart container ── */
    .chart-container {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* ── Level badge ── */
    .level-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }
    .level-error { background: #7f1d1d; color: #fca5a5; }
    .level-warn  { background: #78350f; color: #fcd34d; }
    .level-info  { background: #1e3a5f; color: #93c5fd; }

    /* ── Spinner ── */
    .stSpinner > div {
        border-color: #10b981 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #64748b;
        padding: 0.8rem 1.2rem;
        border: none;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #10b981 !important;
        border-bottom: 2px solid #10b981 !important;
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">⬡ Anomaly Detector</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a log file", type=['log', 'txt'], label_visibility="collapsed")

    st.markdown('<div class="sidebar-section">Detection Tuning</div>', unsafe_allow_html=True)
    contamination = st.slider(
        "Anomaly sensitivity",
        0.01, 0.20, 0.05, 0.01,
        help="Lower = fewer anomalies, higher = more aggressive detection",
        label_visibility="collapsed"
    )
    st.caption(f"Sensitivity: **{contamination:.0%}** of logs flagged")

    st.markdown('<div class="sidebar-section">AI Engine</div>', unsafe_allow_html=True)
    max_explanations = st.slider("Max AI explanations", 1, 15, 5, 1, label_visibility="collapsed")
    st.caption(f"Will generate **{max_explanations}** AI explanations")

    st.markdown(
        '<div class="sidebar-info">'
        '⚡ Engine: Ollama (local)<br>'
        '🧠 Model: llama3.2:3b<br>'
        '💰 Cost: $0.00<br>'
        '🔒 Data: never leaves your machine'
        '</div>',
        unsafe_allow_html=True
    )


# ──────────────────────────────────────────────
# LOAD & PROCESS DATA
# ──────────────────────────────────────────────
if uploaded_file:
    with open("temp_upload.log", "wb") as f:
        f.write(uploaded_file.getbuffer())
    filepath = "temp_upload.log"
else:
    filepath = "data/HDFS_2k.log"

with st.spinner(""):
    df = parse_hdfs_logs(filepath)
    df, feature_cols = engineer_features(df)
    df = detect_anomalies(df, feature_cols, contamination=contamination)


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
total = len(df)
anomaly_count = int(df['is_anomaly'].sum())
anomaly_rate = anomaly_count / total * 100
error_count = int((df['level'] == 'ERROR').sum())

st.markdown(f"""
<div class="main-header">
    <div class="main-title">
        Log Anomaly Detector <span class="main-badge">AI-Powered</span>
    </div>
    <div class="main-subtitle">
        Hybrid detection: Isolation Forest statistical analysis + LLM-powered root cause explanation
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# METRIC CARDS
# ──────────────────────────────────────────────
rate_color = "green" if anomaly_rate < 3 else ("amber" if anomaly_rate < 8 else "red")

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="metric-label">Total Log Lines</div>
        <div class="metric-value">{total:,}</div>
        <div class="metric-detail">Parsed from {'uploaded file' if uploaded_file else 'HDFS_2k.log'}</div>
    </div>
    <div class="metric-card anomaly">
        <div class="metric-label">Anomalies Detected</div>
        <div class="metric-value red">{anomaly_count}</div>
        <div class="metric-detail">Flagged by Isolation Forest (contamination={contamination})</div>
    </div>
    <div class="metric-card rate">
        <div class="metric-label">Anomaly Rate</div>
        <div class="metric-value {rate_color}">{anomaly_rate:.1f}%</div>
        <div class="metric-detail">{'Healthy' if anomaly_rate < 3 else ('Elevated' if anomaly_rate < 8 else 'Critical')} — threshold at {contamination:.0%}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Error-Level Logs</div>
        <div class="metric-value {'red' if error_count > 0 else 'green'}">{error_count}</div>
        <div class="metric-detail">Explicit ERROR entries in source</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CHARTS — TABS
# ──────────────────────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="section-dot blue"></span> Analysis
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊  Distribution", "🧩  Components", "📈  Timeline"])

# ── Color palette ──
colors = {
    'bg': '#111827',
    'grid': '#1e293b',
    'text': '#94a3b8',
    'accent': '#10b981',
    'red': '#ef4444',
    'amber': '#f59e0b',
    'blue': '#3b82f6',
    'purple': '#8b5cf6'
}

plot_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans', color=colors['text'], size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor=colors['grid'], zerolinecolor=colors['grid']),
    yaxis=dict(gridcolor=colors['grid'], zerolinecolor=colors['grid']),
)

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        level_counts = df['level'].value_counts().reset_index()
        level_counts.columns = ['Level', 'Count']
        level_colors = {'INFO': colors['blue'], 'WARN': colors['amber'], 'ERROR': colors['red']}
        fig1 = px.bar(
            level_counts, x='Level', y='Count',
            color='Level',
            color_discrete_map=level_colors,
            title='Log Level Distribution'
        )
        fig1.update_layout(**plot_layout, showlegend=False)
        fig1.update_traces(marker_line_width=0, opacity=0.9)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        anomaly_by_level = df.groupby('level')['is_anomaly'].sum().reset_index()
        anomaly_by_level.columns = ['Level', 'Anomalies']
        fig2 = px.bar(
            anomaly_by_level, x='Level', y='Anomalies',
            color='Level',
            color_discrete_map=level_colors,
            title='Anomalies per Log Level'
        )
        fig2.update_layout(**plot_layout, showlegend=False)
        fig2.update_traces(marker_line_width=0, opacity=0.9)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    top_components = df[df['is_anomaly']]['component'].value_counts().head(10).reset_index()
    top_components.columns = ['Component', 'Anomalies']
    fig3 = px.bar(
        top_components, y='Component', x='Anomalies',
        orientation='h',
        title='Top 10 Anomaly-Producing Components',
        color='Anomalies',
        color_continuous_scale=[[0, colors['blue']], [0.5, colors['purple']], [1, colors['red']]]
    )
    fig3.update_layout(**plot_layout, showlegend=False, coloraxis_showscale=False)
    fig3.update_traces(marker_line_width=0)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    df['line_number'] = range(len(df))
    timeline_data = df[['line_number', 'is_anomaly']].copy()
    timeline_data['is_anomaly_int'] = timeline_data['is_anomaly'].astype(int)

    # rolling window to show anomaly density
    timeline_data['anomaly_density'] = timeline_data['is_anomaly_int'].rolling(window=50, min_periods=1).mean() * 100

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=timeline_data['line_number'],
        y=timeline_data['anomaly_density'],
        mode='lines',
        fill='tozeroy',
        line=dict(color=colors['red'], width=1.5),
        fillcolor='rgba(239, 68, 68, 0.1)',
        name='Anomaly Density'
    ))
    fig4.update_layout(
        **plot_layout,
        title='Anomaly Density Across Log File (rolling window = 50 lines)',
        xaxis_title='Log Line Number',
        yaxis_title='Anomaly %',
        showlegend=False
    )
    st.plotly_chart(fig4, use_container_width=True)


# ──────────────────────────────────────────────
# ANOMALY TABLE
# ──────────────────────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="section-dot red"></span> Detected Anomalies
</div>
""", unsafe_allow_html=True)

anomalies_df = df[df['is_anomaly']][['date', 'time', 'level', 'component', 'message']].reset_index()

st.dataframe(
    anomalies_df,
    use_container_width=True,
    height=400,
    column_config={
        "index": st.column_config.NumberColumn("Line #", width="small"),
        "date": st.column_config.TextColumn("Date", width="small"),
        "time": st.column_config.TextColumn("Time", width="small"),
        "level": st.column_config.TextColumn("Level", width="small"),
        "component": st.column_config.TextColumn("Component", width="medium"),
        "message": st.column_config.TextColumn("Message", width="large"),
    },
    hide_index=True,
)


# ──────────────────────────────────────────────
# AI EXPLANATIONS
# ──────────────────────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="section-dot purple"></span> AI-Powered Root Cause Analysis
</div>
""", unsafe_allow_html=True)

if anomaly_count > 0:
    llm_client = setup_llm()

    for i, (idx, row) in enumerate(anomalies_df.head(max_explanations).iterrows()):
        original_idx = row['index']
        level_class = row['level'].lower()
        badge_html = f'<span class="level-badge level-{level_class}">{row["level"]}</span>'

        with st.expander(f"#{i+1}  ·  {row['component']}  ·  {row['message'][:70]}…"):
            context = get_context_window(df, original_idx)

            # Show the log context in a code block
            st.markdown("**Log Context** (surrounding lines):")
            st.code(context, language="log")

            with st.spinner("🧠 Analyzing with Ollama..."):
                try:
                    explanation = explain_anomaly(llm_client, context)
                except Exception as e:
                    explanation = f"⚠️ Could not generate explanation: {e}"

            st.markdown("**AI Analysis:**")
            st.markdown(explanation)
            st.markdown("---")
else:
    st.info("✅ No anomalies detected at this sensitivity level. Try increasing the slider.")


# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 3rem 0 2rem 0; border-top: 1px solid #1e293b; margin-top: 3rem;">
    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #334155;">
        Built with Isolation Forest + Ollama · Portfolio Project · $0 cost
    </span>
</div>
""", unsafe_allow_html=True)