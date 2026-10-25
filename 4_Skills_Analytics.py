from __future__ import annotations

import plotly.express as px
import streamlit as st

from src import config
from src.analytics import load_all, top_skills
from src.styling import inject_global_css, page_header, render_kpi_row

st.set_page_config(page_title="Skills · " + config.APP_SHORT_TITLE, page_icon="🧠", layout="wide")
inject_global_css()

profiles, submissions, master = load_all()

page_header("Skills Analytics", "Most frequently listed skills across scraped profiles.")

with_skills = int((profiles["skill_count"] > 0).sum())
render_kpi_row([
    ("Profiles With Skills Listed", f"{with_skills:,}", f"of {len(profiles):,} scraped"),
    ("Coverage", f"{with_skills / len(profiles) * 100:.1f}%", "of scraped profiles"),
    ("Distinct Skills", f"{profiles.explode('skills')['skills'].nunique():,}", ""),
])

if with_skills == 0:
    st.warning("No profiles in the current dataset have skills listed.")
    st.stop()

n = st.slider("Number of skills to show", 5, 40, 20)
ts = top_skills(profiles, n=n)

st.markdown('<div class="card">', unsafe_allow_html=True)
fig = px.bar(ts, x="count", y="skill", orientation="h", text="count",
             color="count", color_continuous_scale=[config.COLOR_ACCENT, config.COLOR_PRIMARY])
fig.update_layout(yaxis=dict(autorange="reversed"), height=max(400, n * 22),
                   margin=dict(l=0, r=10, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white",
                   coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("##### Explore Profiles By Skill")
skill_choice = st.selectbox("Pick a skill", ts["skill"].tolist())
matches = profiles[profiles["skills"].map(lambda s: skill_choice in s)]
st.dataframe(
    matches[["name", "srn", "company_clean", "headline", "linkedin_url"]].rename(columns={
        "name": "Name", "srn": "SRN", "company_clean": "Company",
        "headline": "Headline", "linkedin_url": "LinkedIn",
    }),
    use_container_width=True, hide_index=True,
    column_config={"LinkedIn": st.column_config.LinkColumn()},
)
st.markdown("</div>", unsafe_allow_html=True)
