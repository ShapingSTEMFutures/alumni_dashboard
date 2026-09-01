import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(
    page_title="Shaping STEM Futures – Finalist Alumni Dashboard",
    page_icon="🎓",
    layout="wide"
)

# ─── Custom CSS Styling ─────────────────────────────────────────────────────
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
    .obs-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-top: 4px solid #2d7a5f;
        border-radius: 8px;
        padding: 1.2rem;
        height: 100%;
    }
    .obs-card h4 {
        color: #2d7a5f;
        margin: 0 0 0.4rem 0;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .obs-card p {
        color: #4b5563;
        font-size: 0.92rem;
        line-height: 1.4;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Select dataset file dynamically
EXCEL_FILE = "alumni_data_3.xlsx" if os.path.exists("alumni_data_3.xlsx") else "alumni_data.xlsx"

# ─── 1. SAFE IN-MEMORY FILE LOADING ──────────────────────────────────────────
if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ Could not find '{EXCEL_FILE}'. Please verify the file exists in your project directory.")
    st.stop()

try:
    with open(EXCEL_FILE, "rb") as f:
        file_bytes = io.BytesIO(f.read())
    xls = pd.ExcelFile(file_bytes)
    sheet_name = "Alumni Registry" if "Alumni Registry" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(file_bytes, sheet_name=sheet_name)
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

# Dynamic column detection
col_name = next((c for c in df.columns if "Name" in c), df.columns[0])
col_comp = next((c for c in df.columns if "Competition" in c), df.columns[1])
col_year = next((c for c in df.columns if "Year" in c), None)
col_field = next((c for c in df.columns if "Academic" in c or "Field" in c), None)
col_pos = next((c for c in df.columns if "Position" in c or "Current" in c), None)
col_linkedin = next((c for c in df.columns if "LinkedIn" in c), None)

# Clean Award Year
df["Award Year Clean"] = pd.to_numeric(df[col_year], errors="coerce").fillna(2026).astype(int)

# Identify missing or untracked LinkedIn profiles
missing_linkedin_mask = df[col_linkedin].isna() | df[col_linkedin].astype(str).str.strip().isin(['', 'nan', 'NaN', 'None', 'N/A', 'na'])

# Rule: Flag untracked profiles as 'N/A'
df.loc[missing_linkedin_mask, col_field] = "N/A"
df.loc[missing_linkedin_mask, col_pos] = "N/A"
df.loc[missing_linkedin_mask, col_linkedin] = "N/A"

# For profiles WITH LinkedIn but NO listed position, tag as 'N/A (No Position Listed)'
df.loc[~missing_linkedin_mask & (df[col_pos].isna() | (df[col_pos].astype(str).str.strip() == '')), col_pos] = "N/A (No Position Listed)"

# Standardize LinkedIn URLs
df.loc[~missing_linkedin_mask, col_linkedin] = df.loc[~missing_linkedin_mask, col_linkedin].astype(str).str.strip()

# Categorize STEM Domain
def derive_stem_domain(row):
    fld = str(row[col_field]).lower()
    pos = str(row[col_pos]).lower()
    
    if pos == "n/a" and fld == "n/a":
        return "Untracked Profile"
    elif any(k in fld or k in pos for k in ["biotech", "bio", "genetics", "health", "cancer", "medical", "chemist", "microbiology", "life science"]):
        return "Biotechnology & Life Sciences"
    elif any(k in fld or k in pos for k in ["software", "data", "it", "information technology", "computer science", "ai", "ios"]):
        return "Software, AI & Data Systems"
    elif any(k in fld or k in pos for k in ["robotics", "mechatronics", "engineering", "hardware", "automation", "clean energy", "solar", "environmental"]):
        return "Engineering, Robotics & Clean Tech"
    else:
        return "General Science & Education"

df["STEM Domain Cluster"] = df.apply(derive_stem_domain, axis=1)

# Categorize Employment Status
def classify_employment_status(pos):
    val = str(pos).lower()
    if val == "n/a":
        return "N/A (Untracked Profile)"
    elif "n/a (no position" in val:
        return "Not Currently Employed / Seeking Role"
    elif any(k in val for k in ["student", "intern", "tutor", "candidate"]):
        return "Further Study / Academic Training"
    return "Employed (Industry & Research)"

df["Employment Status"] = df[col_pos].apply(classify_employment_status)

# ─── HEADER SECTION ──────────────────────────────────────────────────────────
st.title("Shaping STEM Futures")
st.markdown("#### Finalist Alumni Impact Dashboard")
st.markdown("---")

# ─── 2. METRIC CARDS ─────────────────────────────────────────────────────────
total_alumni = len(df)
verifiable_profiles = len(df[~missing_linkedin_mask])
untracked_profiles = len(df[missing_linkedin_mask])
employed_count = len(df[df["Employment Status"] == "Employed (Industry & Research)"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="label">Total Finalist Alumni</div><div class="value">{total_alumni}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="label">Verifiable LinkedIn Profiles</div><div class="value">{verifiable_profiles}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="label">Untracked Profiles</div><div class="value">{untracked_profiles}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="label">Employed Industry / Research</div><div class="value">{employed_count}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── 3. DATASET OBSERVATION CARDS ───────────────────────────────────────────
st.markdown("### Key Alumni Dataset Observations")

col_obs1, col_obs2, col_obs3 = st.columns(3)

with col_obs1:
    st.markdown("""
    <div class="obs-card">
        <h4>🧬 Discipline Specialization Bias</h4>
        <p><b>Start Talking</b> acts primarily as a pipeline for <b>Biotechnology & Life Sciences</b>, whereas <b>Design for Change</b> feeds into <b>Software Engineering, AI & Data Systems</b>.</p>
    </div>
    """, unsafe_allow_html=True)

with col_obs2:
    st.markdown("""
    <div class="obs-card">
        <h4>🏢 Institutional vs Enterprise Placement</h4>
        <p><i>Start Talking</i> finalists transition into leading medical research institutes (WEHI, Peter Mac, Parexel), while <i>Design for Change</i> finalists move into enterprise tech (News Corp, Agilent, BAE Systems).</p>
    </div>
    """, unsafe_allow_html=True)

with col_obs3:
    st.markdown("""
    <div class="obs-card">
        <h4>🔍 Profile Verification Distribution</h4>
        <p><b>60% of finalists (24/40)</b> maintain publicly verifiable LinkedIn headlines, while <b>40% (16/40)</b> have untracked profile links flagged as <code>N/A</code> across registry fields.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── 4. INTERACTIVE STEM DOMAIN VISUALIZATION ────────────────────────────────
st.markdown("### Interactive STEM Domain & Ecosystem")

col_view_type, col_filter_comp = st.columns(2)

with col_view_type:
    selected_view = st.radio(
        "Select Perspective to Visualize:",
        options=["STEM Domain by Competition Track", "Employment Status Breakdown"],
        horizontal=True
    )

with col_filter_comp:
    comp_filter = st.selectbox(
        "Filter Competition:",
        options=["All Competitions", "Start Talking", "Design for Change"]
    )

if comp_filter != "All Competitions":
    chart_df = df[df[col_comp] == comp_filter]
else:
    chart_df = df

if selected_view == "STEM Domain by Competition Track":
    df_grouped = chart_df.groupby([col_comp, "STEM Domain Cluster"]).size().reset_index(name="Finalist Count")
    
    fig_interactive = px.bar(
        df_grouped,
        x="STEM Domain Cluster",
        y="Finalist Count",
        color=col_comp,
        barmode="group",
        text="Finalist Count",
        title=f"STEM Domain Specialization ({comp_filter})",
        color_discrete_map={
            "Start Talking": "#2d7a5f",
            "Design for Change": "#1a1a2e"
        }
    )
    fig_interactive.update_traces(textposition="outside")
    fig_interactive.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16,
        margin=dict(t=50, b=20),
        xaxis=dict(title="STEM Domain Cluster"),
        yaxis=dict(title="Finalist Count", dtick=2)
    )
else:
    df_emp_grouped = chart_df.groupby([col_comp, "Employment Status"]).size().reset_index(name="Finalist Count")
    
    fig_interactive = px.bar(
        df_emp_grouped,
        x="Employment Status",
        y="Finalist Count",
        color=col_comp,
        barmode="group",
        text="Finalist Count",
        title=f"Employment & Training Status ({comp_filter})",
        color_discrete_map={
            "Start Talking": "#2d7a5f",
            "Design for Change": "#1a1a2e"
        }
    )
    fig_interactive.update_traces(textposition="outside")
    fig_interactive.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16,
        margin=dict(t=50, b=20),
        xaxis=dict(title="Employment Status"),
        yaxis=dict(title="Finalist Count", dtick=2)
    )

st.plotly_chart(fig_interactive, use_container_width=True)

st.markdown("---")

# ─── 5. FINALIST ALUMNI DATA REGISTRY ───────────────────────────────────────
st.markdown("### Finalist Alumni Data Registry")

sector_filter_options = ["All Domains"] + list(df["STEM Domain Cluster"].unique())
selected_sector = st.selectbox("Filter Registry by STEM Domain Cluster:", sector_filter_options)

if selected_sector != "All Domains":
    filtered_df = df[df["STEM Domain Cluster"] == selected_sector]
else:
    filtered_df = df.copy()

display_cols = [col_name, "Award Year Clean", col_comp, col_field, "STEM Domain Cluster", "Employment Status", col_pos, col_linkedin]

registry_table = filtered_df[display_cols].copy()
registry_table.columns = [
    "Full Name", "Award Year", "Competition", "Academic Field",
    "STEM Domain Cluster", "Employment Status", "Current Position", "LinkedIn Profile"
]

st.dataframe(
    registry_table,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("Data: Shaping STEM Futures · Swinburne University of Technology")