"""Run: streamlit run alumni_dashboard.py
Place beside an alumni registry Excel workbook. Requires streamlit, pandas,
plotly and openpyxl. Public search evidence reviewed 3 September 2026.
Full LinkedIn profiles were inaccessible; no complete-history claim is made.
"""
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

PLACEMENTS = json.loads(r'''[{"basis":"Supplied registry","dates":"Aug 2026 appears in registry; start/end not confirmed","name":"Celine Deans","note":"Public profile also mentions an internship with RDD; organisation and whether this is a separate role require clarification.","organisation":"BORNEO Medical Centre","role":"Laboratory Intern","source":"","support":"https://my.linkedin.com/in/celine-amelia-d-5b1322328"},{"basis":"Registry + public LinkedIn search","dates":"Dec 2025 start shown in public result; end not available","name":"Siti Nurmaisara","note":"Registry includes Mar 2026 without defining the date. Public result provides a start month.","organisation":"Chemsain Konsultant Sdn Bhd","role":"Environmental Intern","source":"https://my.linkedin.com/in/siti-nurmaisarah-044621328"},{"basis":"Supplied registry","dates":"Nov 2024 appears in registry; start/end not confirmed","name":"Quoc Trung Doan","note":"No additional conclusive placement evidence retrieved.","organisation":"One Australia Education Group","role":"Software Engineer Internship","source":""},{"basis":"Supplied registry","dates":"Jan 2024 appears in registry; start/end not confirmed","name":"Chloe Thompson","note":"No additional conclusive placement evidence retrieved.","organisation":"CSIRO","role":"Industrial Placement Student","source":""},{"basis":"Public LinkedIn search","dates":"Feb–Jun 2025 · 5 months","name":"Sanchita Vinayagam","note":"Historical internship; kept separate from the registry's Clinical Data Analyst role.","organisation":"Parexel","role":"Intern Clinical Data Analyst","source":"https://my.linkedin.com/in/sanchita-vinayagam"},{"basis":"Public LinkedIn search","dates":"Sep 2023–Feb 2024 · 6 months","name":"Tien Tran","note":"Profile name is Minh Tien Tran; exact supplied profile URL matched.","organisation":"SEAM_ARC","role":"Research Internship","source":"https://au.linkedin.com/in/tm-tien"},{"basis":"Public LinkedIn search","dates":"Dates not available in search result","name":"Jiyang Zhang","note":"Matched exact supplied profile; headline uses Jeffery (Jiyang) Zhang. Completion not confirmed.","organisation":"Komosion","role":"Software Development Intern","source":"https://au.linkedin.com/in/jeffery-jiyang-zhang-0a14aa249"},{"basis":"Public LinkedIn search","dates":"May 2016–Apr 2017 · 1 year","name":"Himeshi Kanchana Abeysekara Loku Kaluarachchilage Dona","note":"Matched exact supplied profile. This placement predates the 2026 award; it is not evidence of program impact.","organisation":"Pearson","role":"Intern — application support","source":"https://lk.linkedin.com/in/himeshi-abeysekara-a59a47b9"},{"basis":"Public LinkedIn search","dates":"3 weeks; dates not available","name":"Charley Kitto","note":"Public result describes guidance from VTHC. Exact job title and dates are not available.","organisation":"Professionals Australia","role":"Internship","source":"https://au.linkedin.com/in/charleyk"},{"basis":"Public LinkedIn search","dates":"1 year; dates not available","name":"Ruby Price","note":"Placement evidence adds context to the registry's Trainee Scientist role; not assumed to be a separate role.","organisation":"St Vincent's Hospital","role":"Working placement — Neurophysiology / Sleep & Respiratory","source":"https://au.linkedin.com/in/ruby-price-736743316"}]''')
STUDY = json.loads(r'''[{"name":"Shan Lu","qualification":"Master of IT","source":"","status":"Qualification recorded; current study unknown"},{"name":"Emily Cheng","qualification":"Master of IT","source":"","status":"Qualification recorded; current study unknown"},{"name":"Stephanie Ling","qualification":"Master of Science (Research)","source":"https://my.linkedin.com/in/stephaniecheahhaoling","status":"Public headline says pursuing"},{"name":"Tien Tran","qualification":"MPhil, Photovoltaic Engineering","source":"https://au.linkedin.com/in/tm-tien","status":"Qualification recorded; current study unknown"},{"name":"Jiyang Zhang","qualification":"Master of IT","source":"https://au.linkedin.com/in/jeffery-jiyang-zhang-0a14aa249","status":"Public headline says student"},{"name":"Indradi Lukman","qualification":"Master of IT, Swinburne","source":"https://au.linkedin.com/in/indradi-lukman","status":"Qualification recorded; current study unknown"}]''')

GREEN = "#2d7a5f"
COLORS = [GREEN, "#52a384", "#b77824", "#e5e7eb"]
STATUS_ORDER = ["Other employment role", "Internship / placement", "Training / possible placement", "No role recorded"]
AREAS = ["Life, environmental & health sciences", "IT & computing", "Engineering & physical sciences", "Law & social sciences", "General science"]

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600&family=DM+Serif+Display&display=swap');
html,body,[data-testid="stAppViewContainer"]{font-family:'DM Sans',sans-serif;background:white;color:#1a1a2e}
h1,h2,h3{font-family:'DM Serif Display',serif!important}
.metric-card{background:#f0f7f4;border-left:4px solid #2d7a5f;border-radius:8px;padding:1.2rem 1.5rem;margin-bottom:.5rem;min-height:155px}
.metric-card .label{font-size:.8rem;color:#6b7280;text-transform:uppercase;letter-spacing:.08em}
.metric-card .value{font-size:2.2rem;font-weight:600;color:#1a1a2e;line-height:1.3}
.metric-card .note{font-size:.78rem;color:#6b7280;line-height:1.5}
.obs-card{background:#fff;border:1px solid #e5e7eb;border-top:4px solid #2d7a5f;border-radius:8px;padding:1.2rem;min-height:170px}
.obs-card h4{color:#2d7a5f;margin:0 0 .4rem;font-size:1.05rem;font-weight:600}
.obs-card p{color:#4b5563;font-size:.92rem;line-height:1.5;margin:0}
.untracked-note{background:#f8faf8;border:1px solid #d6efd8;border-left:4px solid #2d7a5f;border-radius:6px;padding:.8rem 1.2rem;font-size:.9rem;color:#374151;margin:1rem 0}
</style>''', unsafe_allow_html=True)

def meaningful(value):
    if pd.isna(value):
        return False
    return bool(str(value).strip()) and not re.match(r"^(?:n/a\b|nan$|none$|na$)", str(value).strip(), re.I)

def area(field):
    if not meaningful(field):
        return "Not recorded"
    field = str(field).lower()
    for terms, label in [(["biotech", "chemistry", "genetics", "environmental science", "health science"], AREAS[0]), (["information technology", "computer science", "software", "master of it", "cloud computing"], AREAS[1]), (["engineering", "mechatronics", "robotics", "physics", "photovoltaic"], AREAS[2]), (["law", "criminology", "politics", "social justice"], AREAS[3])]:
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

def style_chart(fig):
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font=dict(family="DM Sans", color="#1a1a2e", size=14), margin=dict(l=15,r=25,t=50,b=25))
    return fig

def prepare_data(raw):
    raw = raw.copy()
    raw.columns = raw.columns.astype(str).str.strip()
    def column(terms, required=True):
        result = next((c for c in raw.columns if any(t in c.lower() for t in terms)), None)
        if result is None and required:
            raise ValueError("Missing required column: " + " / ".join(terms))
        return result
    mapping = {"Name":column(["name"]),"Program":column(["competition","activity"]),"Year":column(["year"]),"Academic field":column(["academic","field"]),"Recorded role":column(["position","current"]),"LinkedIn":column(["linkedin"])}
    df = pd.DataFrame({out: raw[col] for out,col in mapping.items()})
    for c in ["Name","Program","Academic field","Recorded role","LinkedIn"]:
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    project = column(["project"], required=False)
    df["Withdrawn"] = raw[project].fillna("").str.contains("withdrawn",case=False) if project else False
    df["Academic area"] = df["Academic field"].apply(area)
    df["Employment evidence"] = df["Recorded role"].apply(classify_employment)
    # Never delete valid academic or job information because LinkedIn is absent.
    pmap = {p["name"]:p for p in PLACEMENTS}
    smap = {p["name"]:p for p in STUDY}
    def placement(row):
        if row["Name"] in pmap:
            return pmap[row["Name"]]
        if row["Employment evidence"] == STATUS_ORDER[1]:
            pieces = row["Recorded role"].split("[",1)
            return dict(name=row["Name"],role=pieces[0],organisation=pieces[1].rstrip("]") if len(pieces)>1 else "Not recorded",dates="Not verified",basis="Supplied registry",source="",note="No additional public verification.")
        return None
    def study(row):
        if row["Name"] in smap:
            return smap[row["Name"]]
        if re.search(r"\bmaster\b|\bmphil\b|\bphd\b|\bdoctor of\b", row["Academic field"], re.I):
            return dict(name=row["Name"],qualification=row["Academic field"],status="Qualification recorded; current study unknown",source="")
        return None
    df["Placement evidence"] = df.apply(placement,axis=1)
    df["Study evidence"] = df.apply(study,axis=1)
    return df

BASE = Path(__file__).resolve().parent
FILENAMES = ["Final_Alumni_Registry_2026.xlsx","alumni_data_5.xlsx","alumni_data_4_2_updated.xlsx","alumni_data_4.xlsx","alumni_data.xlsx"]
excel = next((base/name for base in [BASE,Path.cwd()] for name in FILENAMES if (base/name).exists()),None)
if excel is None:
    st.error("Place your alumni registry Excel file beside this script. Supported names include alumni_data.xlsx and Final_Alumni_Registry_2026.xlsx.")
    st.stop()
try:
    xls = pd.ExcelFile(io.BytesIO(excel.read_bytes()))
    raw = pd.read_excel(xls,sheet_name="Alumni Registry" if "Alumni Registry" in xls.sheet_names else xls.sheet_names[0])
    df = prepare_data(raw)
except Exception as error:
    st.error(f"Could not read the registry: {error}")
    st.stop()

st.title("Shaping STEM Futures")
st.markdown("#### Finalist Alumni Impact Dashboard")
st.divider()
selected = st.selectbox("Activity / Competition",["All Activities"]+sorted(df["Program"].unique()))
view = df if selected=="All Activities" else df[df["Program"]==selected]
n = len(view)
positions = view["Recorded role"].apply(meaningful).sum()
placement_count = view["Placement evidence"].notna().sum()
study_count = view["Study evidence"].notna().sum()
fields = view.loc[view["Academic field"].apply(meaningful),"Academic field"]
finalists = view["Program"].isin(["Start Talking","Design for Change"]).sum()
cards = [("Finalist Alumni*",finalists,"Competition records; finalist status unverified"),("Industry Placements",placement_count,"People with past / present placement evidence"),("Further Study",study_count,"Postgraduate evidence; current enrolment not verified"),("Academic Fields Covered",fields.nunique(),"Distinct original field / qualification labels")]
for col,(label,value,note) in zip(st.columns(4),cards):
    col.markdown(f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div><div class="note">{note}</div></div>',unsafe_allow_html=True)
st.caption("*Study Tour records are excluded from the finalist proxy. Placements can predate awards and are not necessarily completed. Qualifications and employment can overlap.")
missing = (~view["LinkedIn"].apply(meaningful)).sum()
st.markdown(f'<div class="untracked-note">Note on Profile Tracking: <b>{missing/n*100 if n else 0:.1f}%</b> ({missing}/{n}) have no LinkedIn link in the supplied registry. Public searches do not establish complete profile verification.</div>',unsafe_allow_html=True)
st.subheader("Key Alumni & Tour Participant Observations")
tour = df[df["Program"]=="Climate Change Study Tour"]
obs = [("Climate Change Study Tour",f"{len(tour)} registry entries; {int(tour['Withdrawn'].sum())} marked withdrawn. The cohort spans climate science, law, policy and social justice."),("Industry & Research Experience",f"{placement_count} people have placement evidence; {positions} have a role in the original registry. Historical placements are not the same as current employment."),("Academic Field Diversity",f"{fields.nunique()} distinct academic labels across {len(fields)} people. Original field descriptions are retained and grouped into broader areas.")]
for col,(title,body) in zip(st.columns(3),obs):
    col.markdown(f'<div class="obs-card"><h4>{escape(title)}</h4><p>{escape(body)}</p></div>',unsafe_allow_html=True)

st.subheader("Academic Breadth & Employment Pathways")
left,right = st.columns(2)
with left:
    counts = view["Academic area"].value_counts().reindex(AREAS,fill_value=0).rename_axis("Academic area").reset_index(name="People")
    fig=px.bar(counts,x="People",y="Academic area",orientation="h",text="People",title="How many fields are covered?",color_discrete_sequence=[GREEN])
    fig.update_layout(yaxis=dict(autorange="reversed",title=""),xaxis=dict(dtick=1))
    fig.update_traces(textposition="outside",cliponaxis=False)
    st.plotly_chart(style_chart(fig),use_container_width=True)
    st.caption(f"{fields.nunique()} labels grouped into broad areas. {n-len(fields)} people have no academic field recorded.")
    with st.expander("Every recorded academic field"):
        st.dataframe(fields.value_counts().rename_axis("Academic field").reset_index(name="People"),hide_index=True,use_container_width=True)
with right:
    counts=view["Employment evidence"].value_counts().reindex(STATUS_ORDER,fill_value=0)
    fig=go.Figure(go.Pie(labels=counts.index,values=counts.values,hole=.7,sort=False,marker_colors=COLORS,textinfo="none",hovertemplate="%{label}: %{value}<extra></extra>"))
    fig.update_layout(title="Are they employed?",annotations=[dict(text=f"{positions/n*100 if n else 0:.0f}%<br>role listed",showarrow=False,font_size=20)],legend=dict(orientation="h",y=-.1),height=430)
    st.plotly_chart(style_chart(fig),use_container_width=True)
    st.caption(f"{positions}/{n} have a role listed. This is the original registry snapshot, not a verified current employment rate. Missing role ≠ unemployed.")

left,right=st.columns(2)
with left:
    st.markdown("#### Are they doing further study?")
    studies=[s for s in view["Study evidence"] if isinstance(s,dict)]
    pursuing=sum("headline says" in s["status"] for s in studies)
    labels=["Student / pursuing headline","Qualification; current status unknown","No explicit postgraduate evidence"]
    values=[pursuing,len(studies)-pursuing,n-len(studies)]
    fig=go.Figure()
    for label,value,color in zip(labels,values,[GREEN,"#52a384","#e5e7eb"]):
        fig.add_trace(go.Bar(name=label,y=["Study evidence"],x=[value],orientation="h",marker_color=color,text=[value if value else ""],hovertemplate=label+": %{x}<extra></extra>"))
    fig.update_layout(barmode="stack",height=230,legend=dict(orientation="h",y=-.5),xaxis_title="People")
    st.plotly_chart(style_chart(fig),use_container_width=True)
    for s in studies:
        st.write(f"**{s['name']}** — {s['qualification']}")
        st.caption(s["status"])
        if s["source"]:
            st.markdown(f"[Public LinkedIn search source]({s['source']})")
    st.caption("Public headlines can be stale. No current enrolment or post-award progression is independently verified. Internships and tutors are not automatically counted as further study.")
with right:
    st.markdown("#### Placement & internship history")
    for p in view["Placement evidence"]:
        if not isinstance(p,dict):
            continue
        with st.expander(f"{p['name']} — {p['organisation']}"):
            st.write(p["role"])
            st.caption(p["dates"])
            st.write(p["note"])
            if p["source"]:
                st.markdown(f"[{p['basis']}]({p['source']})")
            else:
                st.caption("Source: supplied registry; not independently verified.")
            if p.get("support"):
                st.markdown(f"[Supporting public result]({p['support']})")
    st.caption("Exact supplied profile URLs were used for identity matching. Public results are partial and self-reported. Missing dates and completed status are not inferred.")

comparison=[]
for program,group in view.groupby("Program"):
    for label,value in [("Role in registry",group["Recorded role"].apply(meaningful).sum()),("Placement history",group["Placement evidence"].notna().sum()),("Postgraduate evidence",group["Study evidence"].notna().sum())]:
        comparison.append({"Program":program,"Measure":label,"People":int(value)})
if comparison:
    fig=px.bar(pd.DataFrame(comparison),x="Program",y="People",color="Measure",barmode="group",text="People",title="Pathways by activity",color_discrete_sequence=[GREEN,"#52a384","#a8d5c2"])
    fig.update_layout(legend=dict(orientation="h",y=-.3),yaxis=dict(dtick=1))
    st.plotly_chart(style_chart(fig),use_container_width=True)
st.caption("These measures overlap: employment, placement history and postgraduate study are not mutually exclusive.")

st.subheader("Climate Change Study Tour — Malaysia, 2024")
st.write(f"The full Study Tour cohort contains {len(tour)} registry entries, with {int(tour['Withdrawn'].sum())} marked withdrawn. {tour['Recorded role'].apply(meaningful).sum()} have a role in the original registry and {tour['Placement evidence'].notna().sum()} have placement evidence. This cohort is shown separately from competition finalists.")
st.caption("Attendance, completion and causal program impact are not established by the registry.")

st.subheader("Finalist Alumni & Study Tour Registry")
domain=st.selectbox("Academic area",["All academic areas"]+AREAS+["Not recorded"])
registry=view if domain=="All academic areas" else view[view["Academic area"]==domain]
table=registry[["Name","Year","Program","Academic field","Recorded role","Employment evidence","LinkedIn"]].copy()
table["Placement history"] = registry["Placement evidence"].apply(lambda p:f"{p['role']} — {p['organisation']}" if isinstance(p,dict) else "No conclusive evidence retrieved")
table["Further-study evidence"] = registry["Study evidence"].apply(lambda s:s["qualification"] if isinstance(s,dict) else "Not established")
st.dataframe(table,hide_index=True,use_container_width=True)
with st.expander("Profile-by-profile review notes"):
    audit=[]
    for _,row in df.iterrows():
        p=row["Placement evidence"]
        note="No supplied profile URL; individual review not possible." if not meaningful(row["LinkedIn"]) else "Public search attempted; no conclusive placement evidence retrieved."
        if isinstance(p,dict):
            note="Public placement evidence retrieved; full profile unavailable." if p["source"] else "Registry placement retained; no additional full-profile verification."
        audit.append({"Name":row["Name"],"Review outcome":note})
    st.dataframe(pd.DataFrame(audit),hide_index=True,use_container_width=True)
st.divider()
st.caption(f"Data: {excel.name} · Shaping STEM Futures · Swinburne University of Technology. Public search review: 3 September 2026.")
st.caption("The public-search review covered all 37 profile URLs in the supplied 50-person workbook. Full experience sections were inaccessible. Any additional people in a newer workbook have not been researched. Evidence is matched by name; check names and identity before reusing with another cohort.")
