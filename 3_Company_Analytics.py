from __future__ import annotations

import plotly.express as px
import streamlit as st

from src import config
from src.analytics import company_detail, load_all, top_companies
from src.styling import inject_global_css, page_header

st.set_page_config(page_title="Companies · " + config.APP_SHORT_TITLE, page_icon="🏢", layout="wide")
inject_global_css()

profiles, submissions, master = load_all()

page_header("Company Analytics", "Employers and internships mentioned in student LinkedIn profiles.")

st.info(
    "These figures reflect the **Company** field on each LinkedIn profile at scrape time — "
    "for a graduating class this is mostly internship / part-time employers rather than "
    "confirmed full-time placements. Entries that simply say 'PES University' (not yet "
    "updated) are excluded from company rankings.",
    icon="ℹ️",
)

n = st.slider("Number of companies to show", 5, 50, 20)
tc = top_companies(profiles, n=n)

c1, c2 = st.columns([2, 1])
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Company Rankings")
    fig = px.bar(tc, x="count", y="company", orientation="h", text="count",
                 color="count", color_continuous_scale=["#F58220", "#F58220"])
    fig.update_layout(yaxis=dict(autorange="reversed"), height=max(400, n * 22),
                       margin=dict(l=0, r=10, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white",
                       coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Distribution")
    fig2 = px.sunburst(tc, path=["company"], values="count",
                        color="count", color_continuous_scale=[config.COLOR_ACCENT, config.COLOR_PRIMARY])
    fig2.update_layout(height=max(400, n * 22), margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Drill Into a Company")
selected = st.selectbox("Select a company", tc["company"].tolist())
if selected:
    detail = company_detail(profiles, selected)
    st.write(f"**{len(detail)}** alumni linked to **{selected}**")
    st.dataframe(
        detail.rename(columns={
            "name": "Name", "headline": "Headline", "location": "Location",
            "linkedin_url": "LinkedIn", "connections": "Connections", "followers": "Followers",
        }),
        use_container_width=True, hide_index=True,
        column_config={"LinkedIn": st.column_config.LinkColumn()},
    )
