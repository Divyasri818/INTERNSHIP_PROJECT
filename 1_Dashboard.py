from __future__ import annotations

import plotly.express as px
import streamlit as st

from src import config
from src.analytics import compute_kpis, load_all, scraping_funnel, top_companies, top_skills
from src.styling import inject_global_css, page_header, render_kpi_row

st.set_page_config(page_title="Dashboard · " + config.APP_SHORT_TITLE, page_icon="📊", layout="wide")
inject_global_css()

profiles, submissions, master = load_all()
kpis = compute_kpis(profiles, submissions, master)

page_header("Executive Dashboard", "Full pipeline health and class-wide metrics at a glance.")

render_kpi_row([
    ("Links Submitted", f"{kpis['total_submitted']:,}", "Total form entries"),
    ("Profiles Scraped", f"{kpis['total_scraped']:,}", "Unique SRNs captured"),
    ("Scrape Success Rate", f"{kpis['success_rate']}%", ""),
    ("Failed / Missing", f"{kpis['total_failed']:,}", "Invalid link or scrape error"),
])
st.write("")
render_kpi_row([
    ("Profiles With Employer Signal", f"{kpis['profiles_with_company_signal']:,}", "Real company/internship listed"),
    ("Still Show 'PES University' Only", f"{kpis['profiles_self_reference_only']:,}", "Profile not yet updated"),
    ("No Company Listed", f"{kpis['profiles_no_company_listed']:,}", "Field left blank"),
    ("Companies Represented", f"{kpis['unique_companies']:,}", "Distinct real employers"),
])
st.write("")
render_kpi_row([
    ("Avg. Connections", f"{int(kpis['avg_connections']):,}", "Per profile with data"),
    ("Avg. Followers", f"{int(kpis['avg_followers']):,}", "Per profile with data"),
    ("Profiles With Skills Listed", f"{kpis['profiles_with_skills']:,}", ""),
    ("Avg. Alumni / Company", f"{kpis['avg_alumni_per_company']:,}", "Among represented companies"),
])

st.write("")
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Scraping Funnel Detail")
    funnel = scraping_funnel(master)
    fig = px.pie(funnel, names="status", values="count", hole=0.55,
                 color_discrete_sequence=config.CHART_PALETTE)
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Connections Distribution")
    conn = profiles["connections"].dropna()
    fig2 = px.histogram(conn, nbins=25, color_discrete_sequence=[config.COLOR_PRIMARY])
    fig2.update_layout(showlegend=False, height=380, margin=dict(l=0, r=10, t=10, b=0),
                        xaxis_title="Connections", yaxis_title="Profiles")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

c3, c4 = st.columns(2)
with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Top 15 Companies")
    tc = top_companies(profiles, n=15)
    fig3 = px.treemap(tc, path=["company"], values="count", color="count",
                       color_continuous_scale=[config.COLOR_ACCENT, config.COLOR_PRIMARY])
    fig3.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Top 15 Skills")
    ts = top_skills(profiles, n=15)
    if ts.empty:
        st.info("Skills are listed for only a small subset of profiles - see Skills Analytics for details.")
    else:
        fig4 = px.bar(ts, x="count", y="skill", orientation="h", color_discrete_sequence=[config.COLOR_PRIMARY])
        fig4.update_layout(yaxis=dict(autorange="reversed"), height=380,
                            margin=dict(l=0, r=10, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig4, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
