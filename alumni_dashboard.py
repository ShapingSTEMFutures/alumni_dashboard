import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Shaping STEM Futures – Alumni Dashboard",
    page_icon="🎓",
    layout="wide"
)

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
    .placeholder {
        background: #fff8e1;
        border: 1px dashed #d4a017;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        color: #6b5b00;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

EXCEL_FILE = "alumni_data.xlsx"

st.title("Shaping STEM Futures")
st.markdown("#### Alumni Dashboard")
st.markdown("---")

st.markdown('<div class="placeholder">⚠️ <b>Placeholder dashboard.</b> Real alumni data has not been added yet. Replace the sample data in <code>alumni_data.xlsx</code> to populate this dashboard.</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ─── Load or use sample data ──────────────────────────────────────────────────
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name="Alumni")
else:
    # Sample placeholder data
    df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024, 2025],
        "Alumni Count": [12, 18, 25, 34, 42],
        "Industry Placements": [5, 9, 14, 20, 28],
        "Further Study": [4, 6, 8, 10, 11],
    })

# ─── Metric cards ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="label">Total Alumni</div><div class="value">{df["Alumni Count"].sum()}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="label">Industry Placements</div><div class="value">{df["Industry Placements"].sum()}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="label">Further Study</div><div class="value">{df["Further Study"].sum()}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Charts ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    fig_bar = px.bar(
        df, x="Year", y="Alumni Count", text="Alumni Count",
        color="Alumni Count", color_continuous_scale=["#a8d5c2", "#2d7a5f"],
        title="Alumni Count by Year"
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        showlegend=False, coloraxis_showscale=False,
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16,
        margin=dict(t=50, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    fig_path = px.line(
        df, x="Year", y=["Industry Placements", "Further Study"],
        markers=True, title="Alumni Pathways Over Time",
        color_discrete_map={"Industry Placements": "#2d7a5f", "Further Study": "#a8d5c2"}
    )
    fig_path.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, title=""),
        margin=dict(t=60, b=20)
    )
    st.plotly_chart(fig_path, use_container_width=True)

# ─── Table ────────────────────────────────────────────────────────────────────
st.markdown("#### Alumni Data")
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Data: Shaping STEM Futures · Swinburne University of Technology")