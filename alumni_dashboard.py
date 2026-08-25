import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Shaping STEM Futures – Alumni Dashboard",
    page_icon="🎓",
    layout="wide"
)

# ─── Custom Styling ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600&family=DM+Serif+Display&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'DM Serif Display', serif; }
    .metric-card {
        background: #f0f7f4;
        border-left: 4px solid #2d7a5f;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.5rem;
    }
    .metric-card .label { font-size: 0.8rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-card .value { font-size: 2.2rem; font-weight: 600; color: #1a1a2e; line-height: 1.1; }
</style>
""", unsafe_allow_html=True)

EXCEL_FILE = "alumni_data.xlsx"

# ─── Load Data ───────────────────────────────────────────────────────────────
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name="Alumni Registry")
else:
    st.error(f"❌ Could not find '{EXCEL_FILE}'. Please ensure it is in your project directory.")
    st.stop()

# Clean year data
df["Award Year"] = pd.to_numeric(df["Award Year"], errors="coerce").fillna(2026).astype(int)

# Ensure Pathway Category exists
if "Pathway Category" not in df.columns:
    def classify_pathway(position):
        pos = str(position).lower()
        if any(keyword in pos for keyword in ["student", "candidate", "undergraduate", "postgraduate", "scholar"]):
            return "Further Study"
        return "Industry Placement"
    df["Pathway Category"] = df["Current Position / What They're Doing Now"].apply(classify_pathway)

# ─── Header Section ──────────────────────────────────────────────────────────
st.title("Shaping STEM Futures")
st.markdown("#### Alumni Impact Dashboard")
st.markdown("---")

# ─── 1. METRIC CARDS ─────────────────────────────────────────────────────────
total_alumni = len(df)
industry_placements = len(df[df["Pathway Category"] == "Industry Placement"])
further_study = len(df[df["Pathway Category"] == "Further Study"])
fields_covered = df["Academic / STEM Field Enrolled In"].nunique()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="label">Total Alumni</div><div class="value">{total_alumni}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="label">Industry Placements</div><div class="value">{industry_placements}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="label">Further Study</div><div class="value">{further_study}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="label">Academic Fields Covered</div><div class="value">{fields_covered}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── 2. PARTICIPATION BAR CHART ──────────────────────────────────────────────
st.markdown("### Alumni Participation Over Time")

view_option = st.radio(
    "Select View:",
    options=["Combined Total", "Start Talking", "Design for Change"],
    horizontal=True
)

if view_option == "Start Talking":
    df_chart = df[df["Competition Type"] == "Start Talking"].groupby("Award Year").size().reset_index(name="Alumni Count")
    chart_title = "Start Talking Alumni Count by Year"
    bar_color = "#2d7a5f"
elif view_option == "Design for Change":
    df_chart = df[df["Competition Type"] == "Design for Change"].groupby("Award Year").size().reset_index(name="Alumni Count")
    chart_title = "Design for Change Alumni Count by Year"
    bar_color = "#a8d5c2"
else:
    df_chart = df.groupby("Award Year").size().reset_index(name="Alumni Count")
    chart_title = "Combined Alumni Count by Year (All Competitions)"
    bar_color = "#2d7a5f"

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=df_chart["Award Year"], y=df_chart["Alumni Count"],
    text=df_chart["Alumni Count"], textposition="outside",
    marker_color=bar_color
))

fig_bar.update_layout(
    title=chart_title,
    plot_bgcolor="white", paper_bgcolor="white",
    font_family="DM Sans", title_font_size=16,
    margin=dict(t=50, b=20),
    xaxis=dict(tickmode='linear', dtick=1, tickformat='d')
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ─── 3. COMPETITION GROWTH TREND (SINGLE LINE CHART) ─────────────────────────
st.markdown("### Participant Growth Comparison")

# Build pivot dataframe for line chart
df_growth = df.groupby(["Award Year", "Competition Type"]).size().unstack(fill_value=0).reset_index()
if "Start Talking" not in df_growth.columns:
    df_growth["Start Talking"] = 0
if "Design for Change" not in df_growth.columns:
    df_growth["Design for Change"] = 0

df_growth["Combined Total"] = df_growth["Start Talking"] + df_growth["Design for Change"]

fig_growth = go.Figure()

# Line 1: Combined Total
fig_growth.add_trace(go.Scatter(
    x=df_growth["Award Year"], y=df_growth["Combined Total"],
    mode="lines+markers", name="Combined Total",
    line=dict(color="#1a1a2e", width=3),
    marker=dict(size=8)
))

# Line 2: Start Talking
fig_growth.add_trace(go.Scatter(
    x=df_growth["Award Year"], y=df_growth["Start Talking"],
    mode="lines+markers", name="Start Talking",
    line=dict(color="#2d7a5f", width=2),
    marker=dict(size=8)
))

# Line 3: Design for Change
fig_growth.add_trace(go.Scatter(
    x=df_growth["Award Year"], y=df_growth["Design for Change"],
    mode="lines+markers", name="Design for Change",
    line=dict(color="#a8d5c2", width=2),
    marker=dict(size=8)
))

fig_growth.update_layout(
    title="Participant Growth Over Time (Combined vs Start Talking vs Design for Change)",
    plot_bgcolor="white", paper_bgcolor="white",
    font_family="DM Sans", title_font_size=16,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(t=80, b=20),
    xaxis=dict(tickmode='linear', dtick=1, tickformat='d')
)

st.plotly_chart(fig_growth, use_container_width=True)

st.markdown("---")

# ─── 4. ALUMNI DATA REGISTRY (SHOWS ALL DATA DIRECTLY) ─────────────────────
st.markdown("### Alumni Data Registry")

default_columns = [
    "Full Name", 
    "Award Year", 
    "Academic / STEM Field Enrolled In", 
    "Pathway Category", 
    "Current Position / What They're Doing Now", 
    "LinkedIn Profile"
]

# Renders all records directly without needing a filter
st.dataframe(
    df[default_columns],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("Data: Shaping STEM Futures · Swinburne University of Technology")