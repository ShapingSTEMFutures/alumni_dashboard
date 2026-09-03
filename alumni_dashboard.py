import io
import json
import re
from pathlib import Path
from html import escape
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Shaping STEM Futures – Finalist Alumni Dashboard", page_icon="🎓", layout="wide")

# ─── HARDCODED REGISTRY EVIDENCE BLOCKS ────────────────────────────────────
PLACEMENTS = json.loads(r'''[{"basis":"Supplied registry","dates":"Aug 2026 appears in registry; start/end not confirmed","name":"Celine Deans","note":"Public profile also mentions an internship with RDD; organisation and whether this is a separate role require clarification.","organisation":"BORNEO Medical Centre","role":"Laboratory Intern","source":"","support":"https://my.linkedin.com/in/celine-amelia-d-5b1322328"},{"basis":"Registry + public LinkedIn search","dates":"Dec 2025 start shown in public result; end not available","name":"Siti Nurmaisara","note":"Registry includes Mar 2026 without defining the date. Public result provides a start month.","organisation":"Chemsain Konsultant Sdn Bhd","role":"Environmental Intern","source":"https://my.linkedin.com/in/siti-nurmaisarah-044621328"},{"basis":"Supplied registry","dates":"Nov 2024 appears in registry; start/end not confirmed","name":"Quoc Trung Doan","note":"No additional conclusive placement evidence retrieved.","organisation":"One Australia Education Group","role":"Software Engineer Internship","source":""},{"basis":"Supplied registry","dates":"Jan 2024 appears in registry; start/end not confirmed","name":"Chloe Thompson","note":"No additional conclusive placement evidence retrieved.","organisation":"CSIRO","role":"Industrial Placement Student","source":""},{"basis":"Public LinkedIn search","dates":"Feb–Jun 2025 · 5 months","name":"Sanchita Vinayagam","note":"Historical internship; kept separate from the registry's Clinical Data Analyst role.","organisation":"Parexel","role":"Intern Clinical Data Analyst","source":"https://my.linkedin.com/in/sanchita-vinayagam"},{"basis":"Public LinkedIn search","dates":"Sep 2023–Feb 2024 · 6 months","name":"Tien Tran","note":"Profile name is Minh Tien Tran; exact supplied profile URL matched.","organisation":"SEAM_ARC","role":"Research Internship","source":"https://au.linkedin.com/in/tm-tien"},{"basis":"Public LinkedIn search","dates":"Dates not available in search result","name":"Jiyang Zhang","note":"Matched exact supplied profile; headline uses Jeffery (Jiyang) Zhang. Completion not confirmed.","organisation":"Komosion","role":"Software Development Intern","source":"https://au.linkedin.com/in/jeffery-jiyang-zhang-0a14aa249"},{"basis":"Public LinkedIn search","dates":"May 2016–Apr 2017 · 1 year","name":"Himeshi Kanchana Abeysekara Loku Kaluarachchilage Dona","note":"Matched exact supplied profile. This placement predates the 2026 award; it is not evidence of program impact.","organisation":"Pearson","role":"Intern — application support","source":"https://lk.linkedin.com/in/himeshi-abeysekara-a59a47b9"},{"basis":"Public LinkedIn search","dates":"3 weeks; dates not available","name":"Charley Kitto","note":"Public result describes guidance from VTHC. Exact job title and dates are not available.","organisation":"Professionals Australia","role":"Internship","source":"https://au.linkedin.com/in/charleyk"},{"basis":"Public LinkedIn search","dates":"1 year; dates not available","name":"Ruby Price","note":"Placement evidence adds context to the registry's Trainee Scientist role; not assumed to be a separate role.","organisation":"St Vincent's Hospital","role":"Working placement — Neurophysiology / Sleep & Respiratory","source":"https://au.linkedin.com/in/ruby-price-736743316"}]''')
STUDY = json.loads(r'''[{"name":"Shan Lu","qualification":"Master of IT","source":"","status":"Qualification recorded; current study unknown"},{"name":"Emily Cheng","qualification":"Master of IT","source":"","status":"Qualification recorded; current study unknown"},{"name":"Stephanie Ling","qualification":"Master of Science (Research)","source":"https://my.linkedin.com/in/stephaniecheahhaoling","status":"Public headline says pursuing"},{"name":"Tien Tran","qualification":"MPhil, Photovoltaic Engineering","source":"https://au.linkedin.com/in/tm-tien","status":"Qualification recorded; current study unknown"},{"name":"Jiyang Zhang","qualification":"Master of IT","source":"https://au.linkedin.com/in/jeffery-jiyang-zhang-0a14aa249","status":"Public headline says student"},{"name":"Indradi Lukman","qualification":"Master of IT, Swinburne","source":"https://au.linkedin.com/in/indradi-lukman","status":"Qualification recorded; current study unknown"}]''')

GREEN = "#2d7a5f"
COLORS = [GREEN, "#52a384", "#b77824", "#e5e7eb"]
STATUS_ORDER = ["Other employment role", "Internship / placement", "Training / possible placement", "No role recorded"]
AREAS = ["Life, environmental & health sciences", "IT & computing", "Engineering & physical sciences", "Law & social sciences", "General science"]

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');
html,body,[data-testid="stAppViewContainer"]{font-family:'DM Sans',sans-serif;background-color:#ffffff;color:#1a1a2e;}
h1,h2,h3,h4{font-family:'DM Serif Display',serif!important;color:#111827;}

.metric-card {
    background: #f8faf9;
    border: 1px solid #e5e7eb;
    border-left: 4px solid #2d7a5f;
    border-radius: 6px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.5rem;
    min-height: 120px;
}
.metric-card .label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 0.25rem; }
.metric-card .value { font-size: 2.75rem; font-weight: 600; color: #111827; line-height: 1.1; font-family: 'DM Sans', sans-serif; }
.metric-card .note { font-size: 0.78rem; color: #6b7280; margin-top: 0.4rem; }

.badge { background: #e6f2ed; color: #2d7a5f; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 500; float: right; margin-top: 5px; }
.section-title { font-size: 2rem; margin-bottom: 0.2rem; }
.section-subtitle { font-size: 0.9rem; color: #6b7280; margin-bottom: 1.2rem; }

.progress-bar-container { width: 100%; display: flex; align-items: center; margin-bottom: 0.8rem; }
.progress-bar-label { flex: 1; font-size: 0.9rem; color: #374151; }
.progress-bar-val { font-weight: 600; color: #111827; margin-left: 10px; font-size: 0.9rem; }
.progress-track { width: 100%; background-color: #f3f4f6; border-radius: 4px; height: 12px; margin-top: 4px; }
.progress-fill { height: 100%; background-color: #2d7a5f; border-radius: 4px; }

.info-box { background-color: #f4fbf7; border-radius: 6px; padding: 1rem 1.25rem; color: #2d7a5f; font-size: 0.95rem; margin-top: 1rem; }
.info-box-text { color: #6b7280; font-size: 0.85rem; margin-top: 0.75rem; line-height: 1.4; }

.tour-box { background: #f8faf9; border-left: 4px solid #2d7a5f; padding: 2rem; border-radius: 6px; margin-top: 1.5rem; margin-bottom: 1.5rem;}
.tour-stats { display: flex; justify-content: space-around; text-align: left; margin-top: 0.5rem;}
.tour-stat-val { font-size: 2.2rem; font-weight: 500; color: #2d7a5f; line-height: 1.1; font-family: 'DM Serif Display', serif; }
.tour-stat-label { font-size: 0.85rem; color: #6b7280; margin-top: 0.2rem; }
.tour-desc { color: #374151; font-size: 0.95rem; line-height: 1.6; margin-top: 1.5rem; }
.tour-caption { color: #6b7280; font-size: 0.8rem; margin-top: 1rem; line-height: 1.4; }
.untracked-note { background:#f8faf8; border:1px solid #d6efd8; border-left:4px solid #2d7a5f; border-radius:6px; padding:.8rem 1.2rem; font-size:.9rem; color:#374151; margin:1rem 0; }
</style>''', unsafe_allow_html=True)

# ─── FLEXIBLE PARSING HELPERS ──────────────────────────────────────────────
def meaningful(value):
    if pd.isna(value):
        return False
    return bool(str(value).strip()) and not re.match(r"^(?:n/a\b|nan$|none$|na$)", str(value).strip(), re.I)

def area(field):
    if not meaningful(field):
        return "Not recorded"
    field = str(field).lower()
    for terms, label in [(["biotech", "chemistry", "genetics", "environmental science", "health science"], AREAS[0]), 
                         (["information technology", "computer science", "software", "master of it", "cloud computing", "data analytics", "network design"], AREAS[1]), 
                         (["engineering", "mechatronics", "robotics", "physics", "photovoltaic"], AREAS[2]), 
                         (["law", "criminology", "politics", "social justice", "llb"], AREAS[3])]:
        if any(term in field for term in terms):
            return label
    return AREAS[4]

def classify_employment(position):
    if not meaningful(position):
        return STATUS_ORDER[3]
    title = str(position).split("[")[0]
    if re.search(r"\bintern(?:ship)?\b|\bplacement\b", title, re.I):
        return STATUS_ORDER[1]
    if re.search(r"\btrainee\b|\bvoaction\b", title, re.I):
        return STATUS_ORDER[2]
    return STATUS_ORDER[0]

@st.cache_data
def load_data():
    BASE = Path(__file__).resolve().parent
    FILENAMES = ["alumni_data.xlsx"]
    excel = next((base/name for base in [BASE, Path.cwd()] for name in FILENAMES if (base/name).exists()), None)

    if excel is None:
        return None, None

    xls = pd.ExcelFile(io.BytesIO(excel.read_bytes()))
    sheet = "Alumni Registry" if "Alumni Registry" in xls.sheet_names else xls.sheet_names[0]
    raw = pd.read_excel(xls, sheet_name=sheet)
    raw.columns = raw.columns.astype(str).str.strip()

    def column(terms, required=False):
        for c in raw.columns:
            clean_c = c.lower().strip()
            if any(t in clean_c for t in terms):
                return c
        return None

    c_name = column(["name"]) or raw.columns[0]
    c_prog = column(["competition", "activity", "program"]) or raw.columns[1]
    c_year = column(["year", "award"])
    c_field = column(["academic", "field"])
    c_role = column(["job", "position", "current", "role"])
    c_link = column(["linkedin"])

    df = pd.DataFrame()
    df["Name"] = raw[c_name].fillna("").astype(str).str.strip()
    df["Program"] = raw[c_prog].fillna("General Cohort").astype(str).str.strip()
    df["Year"] = pd.to_numeric(raw[c_year], errors="coerce").astype("Int64") if c_year else None
    df["Academic field"] = raw[c_field].fillna("").astype(str).str.strip() if c_field else ""
    df["Recorded role"] = raw[c_role].fillna("").astype(str).str.strip() if c_role else ""
    df["LinkedIn"] = raw[c_link].fillna("").astype(str).str.strip() if c_link else ""

    project = column(["project"])
    df["Withdrawn"] = raw[project].fillna("").str.contains("withdrawn", case=False) if project else False
    df["Academic area"] = df["Academic field"].apply(area)
    df["Employment evidence"] = df["Recorded role"].apply(classify_employment)

    pmap = {p["name"]: p for p in PLACEMENTS}
    smap = {p["name"]: p for p in STUDY}

    def placement(row):
        if row["Name"] in pmap:
            return pmap[row["Name"]]
        if row["Employment evidence"] == STATUS_ORDER[1]:
            pieces = row["Recorded role"].split("[", 1)
            return dict(name=row["Name"], role=pieces[0], organisation=pieces[1].rstrip("]") if len(pieces)>1 else "Not recorded")
        return None

    def study(row):
        if row["Name"] in smap:
            return smap[row["Name"]]
        if re.search(r"\bmaster\b|\bmphil\b|\bphd\b|\bdoctor of\b", row["Academic field"], re.I):
            return dict(name=row["Name"], qualification=row["Academic field"], status="Qualification recorded")
        return None

    df["Placement evidence"] = df.apply(placement, axis=1)
    df["Study evidence"] = df.apply(study, axis=1)

    return df, excel.name

df, excel_filename = load_data()

if df is None:
    st.error("Place your alumni registry Excel file beside this script. Supported names include alumni_data.xlsx and Final_Alumni_Registry_2026.xlsx.")
    st.stop()

# ─── HEADER ────────────────────────────────────────────────────────────────
st.title("Shaping STEM Futures")
st.markdown("#### Finalist Alumni Impact Dashboard")
st.divider()

# Interactive Activity Filter Dropdown
all_activities = ["All Activities"] + sorted([p for p in df["Program"].unique() if p])
selected_activity = st.selectbox("Activity Filter", all_activities)

view = df if selected_activity == "All Activities" else df[df["Program"] == selected_activity]
n = len(view)
positions = view["Recorded role"].apply(meaningful).sum()
placement_count = view["Placement evidence"].notna().sum()
study_count = view["Study evidence"].notna().sum()
fields = view.loc[view["Academic field"].apply(meaningful), "Academic field"]
finalists = view["Program"].isin(["Start Talking", "Design for Change"]).sum()

# ─── TOP METRIC CARDS ──────────────────────────────────────────────────────
cols = st.columns(4)
cards = [
    ("FINALIST ALUMNI", finalists if selected_activity == "All Activities" else len(view[view["Program"].isin(["Start Talking", "Design for Change"])])),
    ("INDUSTRY PLACEMENTS", placement_count),
    ("FURTHER STUDY", study_count),
    ("ACADEMIC FIELDS COVERED", fields.nunique())
]

for i, (label, val) in enumerate(cards):
    cols[i].markdown(f'''
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{val}</div>
    </div>
    ''', unsafe_allow_html=True)

missing = (~view["LinkedIn"].apply(meaningful)).sum()
st.markdown(f'<div class="untracked-note">Note on Profile Tracking: <b>{missing/n*100 if n else 0:.1f}%</b> ({missing}/{n}) have no LinkedIn link. Public searches do not establish complete profile verification.</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── ACADEMIC & EMPLOYMENT ROW ────────────────────────────────────
col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:
    st.markdown('<div class="badge">5 broad areas</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">How many fields are covered?</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-subtitle">{fields.nunique()} recorded academic labels · {len(fields)} people with academic information · {n - len(fields)} not recorded.</div>', unsafe_allow_html=True)
    
    counts = view["Academic area"].value_counts().reindex(AREAS, fill_value=0)
    max_count = max(1, counts.max())
    
    bar_colors = {
        AREAS[0]: "#2d7a5f",
        AREAS[1]: "#4b9c81",
        AREAS[2]: "#79a3b1",
        AREAS[3]: "#a3b8a3",
        AREAS[4]: "#ccd4cc"
    }
    
    for area_name in AREAS:
        count = counts[area_name]
        pct = (count / max_count) * 100
        color = bar_colors.get(area_name, "#2d7a5f")
        st.markdown(f'''
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between;">
                <span class="progress-bar-label">{area_name}</span>
                <span class="progress-bar-val">{count}</span>
            </div>
            <div class="progress-track"><div class="progress-fill" style="width: {pct}%; background-color: {color};"></div></div>
        </div>
        ''', unsafe_allow_html=True)
        
    with st.expander("▼ See every recorded academic field"):
        field_df = fields.value_counts().rename_axis("Academic field").reset_index(name="Count")
        st.dataframe(field_df, hide_index=True, use_container_width=True)

with col_right:
    st.markdown('<h2 class="section-title">Are they employed?</h2>', unsafe_allow_html=True)
    
    emp_counts = view["Employment evidence"].value_counts().reindex(STATUS_ORDER, fill_value=0)
    pct_employed = (positions / n) * 100 if n else 0
    
    fig = go.Figure(go.Pie(
        labels=emp_counts.index, 
        values=emp_counts.values, 
        hole=0.68, 
        sort=False, 
        marker_colors=COLORS, 
        textinfo="none",
        hovertemplate="%{label}: %{value}<extra></extra>"
    ))
    fig.update_layout(
        annotations=[dict(text=f"<b>{pct_employed:.0f}%</b><br><span style='font-size:12px;color:#6b7280;'>have a role listed</span>", showarrow=False, font_size=32)],
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=13, color="#374151")),
        margin=dict(t=10, b=10, l=0, r=0),
        height=260,
        paper_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown(f'''
    <div class="info-box">
        {positions} of {n} have a role in the supplied registry, including {emp_counts.get(STATUS_ORDER[1], 0)} explicit placements. Historical internships are separate and do not change this snapshot.
    </div>
    <div class="info-box-text">
        Listed roles are evidence of employment or work experience, not a verified employment rate. No position listed does not mean unemployed.
    </div>
    ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── PATHWAYS BY ACTIVITY ROW ─────────────────────────────────────────────
st.markdown('<h2 class="section-title">Pathways by activity</h2>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">People with a role in the registry, placement history, or postgraduate-study evidence. These measures overlap and must not be added together.</div>', unsafe_allow_html=True)

pathway_data = []
programs = ["Start Talking", "Design for Change", "Climate Change Study Tour"]
for prog in programs:
    group = view[view["Program"] == prog] if selected_activity == "All Activities" else view
    if selected_activity != "All Activities" and prog != selected_activity:
        continue
    if len(group) == 0: continue
    pathway_data.append({
        "Program": f"{prog} ({len(group)} records)",
        "Role in registry": group["Recorded role"].apply(meaningful).sum(),
        "Placement history": group["Placement evidence"].notna().sum(),
        "Postgraduate evidence": group["Study evidence"].notna().sum()
    })

for row in pathway_data:
    st.markdown(f'<div style="font-weight: 600; font-size: 1.05rem; color: #111827; margin-top: 1.2rem; margin-bottom: 0.6rem;">{row["Program"]}</div>', unsafe_allow_html=True)
    max_val = max(15, row["Role in registry"])
    
    bars = [
        ("Role in registry", row["Role in registry"], "#2d7a5f"),
        ("Placement history", row["Placement history"], "#52a384"),
        ("Postgraduate evidence", row["Postgraduate evidence"], "#c6e2d6")
    ]
    
    for label, val, color in bars:
        pct = (val / max_val) * 100 if max_val > 0 else 0
        st.markdown(f'''
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 180px; font-size: 0.9rem; color: #374151;">{label}</div>
            <div style="flex-grow: 1; margin: 0 15px;">
                <div style="width: 100%; background-color: #f3f4f6; border-radius: 4px; height: 14px;">
                    <div style="width: {pct}%; background-color: {color}; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            <div style="width: 30px; text-align: right; font-weight: 600; font-size: 0.9rem;">{val}</div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── BEYOND THE COMPETITIONS (STUDY TOUR) ─────────────────────────────────
tour = df[df["Program"] == "Climate Change Study Tour"]
st.markdown(f'''
<div class="tour-box">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div style="flex: 1;">
            <div style="font-size: 0.75rem; letter-spacing: 0.1em; color: #2d7a5f; text-transform: uppercase; font-weight: 600;">BEYOND THE COMPETITIONS · 2024</div>
            <h2 style="font-family: 'DM Serif Display', serif; font-size: 2.3rem; margin: 0.4rem 0; color: #111827; line-height: 1.1;">Climate Change<br>Study Tour, Malaysia</h2>
            <div style="color: #6b7280; font-size: 1rem; margin-top: 0.8rem;">A separate cohort connecting climate science<br>with law, policy and social justice.</div>
        </div>
        <div style="flex: 1.5; padding-left: 2rem;">
            <div class="tour-stats">
                <div>
                    <div class="tour-stat-val">{len(tour)}</div>
                    <div class="tour-stat-label">registry entries</div>
                </div>
                <div>
                    <div class="tour-stat-val">{len(tour) - int(tour['Withdrawn'].sum())} + {int(tour['Withdrawn'].sum())}</div>
                    <div class="tour-stat-label">not marked withdrawn + withdrawn</div>
                </div>
                <div>
                    <div class="tour-stat-val">{tour.loc[tour['Academic field'].apply(meaningful), 'Academic field'].nunique()}</div>
                    <div class="tour-stat-label">academic labels across {tour['Academic field'].apply(meaningful).sum()} people</div>
                </div>
            </div>
            <div class="tour-desc">
                Five people have a role listed: three other employment roles, one CSIRO placement and one trainee scientist role at St Vincent's Health Australia. Placement history is now recorded for three tour members: Chloe Thompson (CSIRO), Ruby Price (St Vincent's) and Charley Kitto (Professionals Australia). Current further-study status is not established.
            </div>
            <div class="tour-caption">
                Study Tour figures always show the full 2024 cohort. Nine entries are not marked withdrawn; attendance or completion is not independently confirmed.
            </div>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)

# ─── ALUMNI REGISTRY DATA VIEWER ──────────────────────────────────────────
st.markdown('<h2 class="section-title" style="margin-top: 2rem;">Alumni registry</h2>', unsafe_allow_html=True)

col_filters_left, col_filters_right = st.columns([3, 1])
with col_filters_right:
    domain = st.selectbox("Academic area", ["All academic areas"] + AREAS + ["Not recorded"])

registry = view if domain == "All academic areas" else view[view["Academic area"] == domain]
st.markdown(f'<div class="section-subtitle">{len(registry)} records · Program and academic-area filters applied. Original role wording is retained.</div>', unsafe_allow_html=True)

table = registry[["Name", "Year", "Program", "Academic field", "Recorded role", "LinkedIn"]].copy()
table["Name / year"] = table.apply(lambda r: f"{r['Name']}\n{r['Year'] if pd.notna(r['Year']) else ''}", axis=1)
table["Recorded role"] = table["Recorded role"].replace("", "Not recorded")

st.dataframe(
    table[["Name / year", "Program", "Academic field", "Recorded role"]],
    hide_index=True,
    use_container_width=True,
    height=350
)

st.divider()
st.caption(f"Data: {excel_filename} · Shaping STEM Futures · Swinburne University of Technology.")