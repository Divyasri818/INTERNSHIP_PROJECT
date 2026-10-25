"""
PES University Alumni Intelligence Platform - main entrypoint.

Run locally:    streamlit run app.py
Docs:           see README.md
"""
from __future__ import annotations
from PIL import Image

import datetime as dt


import pandas as pd
import plotly.express as px
import streamlit as st

from src import config
from src.analytics import compute_kpis, load_all, top_companies
from src.styling import inject_global_css, render_kpi_row
import base64
from pathlib import Path

def image_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()
    
st.set_page_config(
    page_title=config.APP_SHORT_TITLE,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()

logo_base64 = image_to_base64("assets/pes_logo.png")
banner_base64 = image_to_base64("assets/pes_background.jpg")

# ---------------------------------------------------------------------------
# Landing / splash page — shown once at the very start of a session, and
# rendered BEFORE the (slower) data load below so it paints immediately
# instead of the dashboard flashing first while data loads.
# Clicking "Get started" (a link that sets ?entered=true) reveals the
# dashboard. Uses assets/pes_background.jpg for the right-hand photo.
# ---------------------------------------------------------------------------
if st.query_params.get("entered") == "true":
    st.session_state["entered_app"] = True

if not st.session_state.get("entered_app", False):
    st.markdown(
        f"""
        <style>
            html, body {{margin: 0 !important; padding: 0 !important; overflow: hidden !important;}}
            #MainMenu, header[data-testid="stHeader"], footer {{visibility: hidden; display: none;}}
            [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{display: none;}}
            section[data-testid="stSidebar"] {{display: none;}}
            [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{padding: 0 !important; overflow: hidden !important;}}
            .block-container, [data-testid="stMainBlockContainer"] {{padding: 0 !important; max-width: 100% !important;}}
            [data-testid="stVerticalBlock"] {{gap: 0 !important;}}
            [data-testid="element-container"] {{margin: 0 !important;}}
            .stApp {{background: white; height: 100vh; overflow: hidden;}}

            .landing-wrap {{
                margin-left: calc(-50vw + 50%);
                margin-right: calc(-50vw + 50%);
                width: 100vw;
                height: 100vh;
                display: flex;
                flex-wrap: nowrap;
                overflow: hidden;
            }}
            .landing-left, .landing-right {{
                flex: 1 1 50%;
                height: 100vh;
                position: relative;
                box-sizing: border-box;
            }}
            .landing-left {{
                background: #F1F2F4;
                padding: 5vh 60px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .landing-logo {{
                width: 64px;
                height: 64px;
                border-radius: 14px;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,.08);
                padding: 8px;
                margin-bottom: 36px;
            }}
            .landing-kicker {{
                color: {config.COLOR_ACCENT};
                font-weight: 700;
                letter-spacing: 1.5px;
                font-size: .8rem;
                text-transform: uppercase;
                margin-bottom: 14px;
            }}
            .landing-left h1 {{
                font-family: 'Poppins', sans-serif;
                font-size: 3rem;
                font-weight: 800;
                color: {config.COLOR_PRIMARY};
                line-height: 1.15;
                margin: 0 0 18px 0;
            }}
            .landing-left p {{
                color: {config.COLOR_MUTED};
                font-size: 1.05rem;
                line-height: 1.6;
                max-width: 480px;
                margin-bottom: 34px;
            }}
            .landing-cta {{
                display: inline-flex;
                align-items: center;
                gap: 10px;
                background: {config.COLOR_ACCENT};
                color: white !important;
                font-weight: 700;
                font-size: 1rem;
                padding: 14px 26px;
                border-radius: 12px;
                text-decoration: none !important;
                width: fit-content;
                box-shadow: 0 8px 20px rgba(245,130,32,.35);
                transition: .2s;
            }}
            .landing-cta:hover {{
                background: {config.COLOR_PRIMARY};
                box-shadow: 0 8px 20px rgba(11,31,58,.35);
            }}
            .landing-copyright {{
                color: #9AA1AC;
                font-size: .8rem;
                margin-top: 60px;
            }}

            .landing-right {{
                background:
                    linear-gradient(rgba(0,0,0,.15), rgba(0,0,0,.45)),
                    url("data:image/jpeg;base64,{banner_base64}");
                background-size: cover;
                background-position: center;
                padding: 50px 55px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                color: white;
            }}
            .landing-quote {{
                font-size: 1.7rem;
                font-weight: 600;
                line-height: 1.35;
                max-width: 520px;
            }}
            .landing-quote .qmark {{
                color: {config.COLOR_ACCENT};
                font-size: 2rem;
                font-weight: 800;
                line-height: 0;
                vertical-align: -6px;
                margin-right: 2px;
            }}
            .landing-stats {{
                display: flex;
                gap: 1px;
                background: rgba(255,255,255,.25);
                border-radius: 14px;
                overflow: hidden;
                width: fit-content;
                backdrop-filter: blur(6px);
            }}
            .landing-stat {{
                background: rgba(11,31,58,.55);
                padding: 16px 26px;
                min-width: 140px;
            }}
            .landing-stat .num {{
                font-size: 1.6rem;
                font-weight: 800;
            }}
            .landing-stat .label {{
                font-size: .72rem;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #D9DEE6;
                margin-top: 2px;
            }}

            @media (max-width: 900px) {{
                html, body, .stApp {{overflow: auto !important; height: auto !important;}}
                .landing-wrap {{ flex-wrap: wrap; height: auto; overflow: visible; }}
                .landing-left, .landing-right {{ height: auto; min-height: 60vh; padding: 40px 32px; }}
                .landing-left h1 {{ font-size: 2.2rem; }}
                .landing-quote {{ font-size: 1.3rem; }}
            }}
        </style>

        <div class="landing-wrap">
            <div class="landing-left">
                <img src="data:image/png;base64,{logo_base64}" class="landing-logo">
                <div class="landing-kicker">Alumni Relations &middot; PES University</div>
                <h1>See where every graduate landed.</h1>
                <p>One workspace for the class's LinkedIn footprint &mdash; employer signal, skills coverage, and the health of the data behind it.</p>
                <a href="?entered=true" target="_self" class="landing-cta">Get started &rarr;</a>
                <div class="landing-copyright">&copy; {config.ORG_NAME}, Bengaluru, India.</div>
            </div>
            <div class="landing-right">
                <div class="landing-quote"><span class="qmark">&ldquo;</span>Every batch leaves a trail. This is where PES follows it.<span class="qmark">&rdquo;</span></div>
                <div class="landing-stats">
                    <div class="landing-stat">
                        <div class="num">50+</div>
                        <div class="label">Years of Legacy</div>
                    </div>
                    <div class="landing-stat">
                        <div class="num">97+</div>
                        <div class="label">Companies Mapped</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------------------
# Past this point the user has clicked "Get started" — load data now.
# ---------------------------------------------------------------------------
try:
    profiles, submissions, master = load_all()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

kpis = compute_kpis(profiles, submissions, master)

st.markdown(
    f"""
<style>

.hero {{
    background:
        linear-gradient(rgba(0,0,0,.65), rgba(0,0,0,.65)),
        url("data:image/jpeg;base64,{banner_base64}");

    background-size: cover;
    background-position: center;

    border-radius: 20px;

    padding: 80px 60px;

    text-align: center;

    color: white;

    margin-bottom: 30px;

    box-shadow: 0 8px 30px rgba(0,0,0,.25);
}}

.hero-logo {{

    width:120px;

    background:white;

    padding:12px;

    border-radius:18px;

    margin-bottom:20px;

}}

.badge {{

    display:inline-block;

    background:rgba(255,255,255,.15);

    padding:8px 18px;

    border-radius:999px;

    margin-bottom:18px;

    color:white;

    font-weight:600;

}}

.hero h1 {{

    font-size:3.2rem;

    margin-bottom:12px;

}}

.hero p {{

    font-size:1.2rem;

    max-width:850px;

    margin:auto;

}}

</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Hero Section
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Hero Section
# ---------------------------------------------------------------------------

st.markdown(
    f"""
<div class="hero">

<img src="data:image/png;base64,{logo_base64}" class="hero-logo">

<div class="badge">
🎓 {config.ORG_NAME} · Class of 2026
</div>

<h1>{config.APP_TITLE}</h1>

<p>
A live analytics layer over the graduating class's LinkedIn footprint —
profile coverage, employer & internship signal, skills,
and the health of the data collection pipeline.
</p>

</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI grid
# ---------------------------------------------------------------------------
st.markdown("### Overview")
render_kpi_row(
    [
        ("Links Submitted", f"{kpis['total_submitted']:,}", "Google Form entries"),
        ("Profiles Scraped", f"{kpis['total_scraped']:,}", "Successfully captured"),
        ("Scrape Success Rate", f"{kpis['success_rate']}%", "Scraped ÷ submitted"),
        ("Failed / Missing", f"{kpis['total_failed']:,}", "Invalid link or scrape error"),
    ]
)
st.write("")
render_kpi_row(
    [
        ("Companies Represented", f"{kpis['unique_companies']:,}", "Excludes self-referencing 'PES University' entries"),
        ("Locations Captured", f"{kpis['unique_locations']:,}", "Distinct location strings"),
        ("Avg. Connections", f"{int(kpis['avg_connections']):,}", "Per profile with data"),
        ("Avg. Followers", f"{int(kpis['avg_followers']):,}", "Per profile with data"),
    ]
)

st.write("")

# ---------------------------------------------------------------------------
# Quick charts
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Scraping Funnel")
    funnel = master["scrape_status"].value_counts().rename_axis("status").reset_index(name="count")
    fig = px.bar(
        funnel, x="count", y="status", orientation="h", text="count",
        color="status", color_discrete_sequence=config.CHART_PALETTE,
    )
    fig.update_layout(showlegend=False, height=320, margin=dict(l=0, r=10, t=10, b=0),
                       plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Top Companies & Internships Mentioned")
    tc = top_companies(profiles, n=10)
    fig2 = px.bar(
        tc, x="count", y="company", orientation="h", text="count",
        color_discrete_sequence=[config.COLOR_PRIMARY],
    )
    fig2.update_layout(yaxis=dict(autorange="reversed"), height=320,
                        margin=dict(l=0, r=10, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Quick navigation
# ---------------------------------------------------------------------------
st.markdown("### Explore the platform")
nav_cols = st.columns(4)
nav_items = [
    ("📊", "Dashboard", "Executive KPIs & trends", "pages/1_Dashboard.py"),
    ("👥", "Alumni Directory", "Search, filter, export", "pages/2_Alumni_Directory.py"),
    ("🏢", "Company Analytics", "Employers & internships", "pages/3_Company_Analytics.py"),
    ("🧠", "Skills Analytics", "Most common skills", "pages/4_Skills_Analytics.py"),
]
for col, (icon, title, desc, target) in zip(nav_cols, nav_items):
    with col:
        st.markdown(
            f'<div class="card" style="text-align:center;">'
            f'<div style="font-size:1.8rem;">{icon}</div>'
            f'<b>{title}</b><br><span style="color:{config.COLOR_MUTED};font-size:0.85rem;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.page_link(target, label=f"Open {title} →")

st.markdown(
    f"""
    <div style="text-align:center; color:{config.COLOR_MUTED}; font-size:0.8rem; margin-top:2rem; padding-top:1rem; border-top:1px solid rgba(31,27,30,0.08);">
        Built for {config.ORG_NAME} · Data sourced from student-submitted LinkedIn links, collected via Google Form and processed with a public-profile scraper ·
        This is not an official PES University product unless formally adopted.
    </div>
    """,
    unsafe_allow_html=True,
)
