from __future__ import annotations

import plotly.express as px
import streamlit as st

from src import config
from src.analytics import compute_kpis, failed_records, failure_breakdown, load_all, scraping_funnel
from src.styling import inject_global_css, page_header, render_kpi_row

st.set_page_config(page_title="Data Quality · " + config.APP_SHORT_TITLE, page_icon="📉", layout="wide")
inject_global_css()

profiles, submissions, master = load_all()
kpis = compute_kpis(profiles, submissions, master)

page_header("Scraping & Data Quality", "Health of the collection pipeline: what was submitted, what was captured, and why the rest failed.")

render_kpi_row([
    ("Total Links Submitted", f"{kpis['total_submitted']:,}", "Unique SRNs in the form"),
    ("Successfully Scraped", f"{kpis['total_scraped']:,}", ""),
    ("Failed / Missing", f"{kpis['total_failed']:,}", ""),
    ("Success Rate", f"{kpis['success_rate']}%", ""),
])

st.write("")
c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Funnel: Submitted → Scraped / Failed")
    funnel = scraping_funnel(master)
    fig = px.funnel(
        funnel.sort_values("count", ascending=False), x="count", y="status",
        color_discrete_sequence=[config.COLOR_PRIMARY],
    )
    fig.update_layout(height=360, margin=dict(l=0, r=10, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Failure Reasons")
    fb = failure_breakdown(master)
    if fb.empty:
        st.success("No failures recorded 🎉")
    else:
        fig2 = px.pie(fb, names="reason", values="count", hole=0.5,
                      color_discrete_sequence=config.CHART_PALETTE)
        fig2.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.3))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Failed / Missing Records")
failed_df = failed_records(master)
st.write(f"**{len(failed_df):,}** records did not produce a scraped profile.")

reason_filter = st.multiselect("Filter by reason", sorted(failed_df["failure_reason"].dropna().unique().tolist()))
view = failed_df[failed_df["failure_reason"].isin(reason_filter)] if reason_filter else failed_df

st.dataframe(
    view.rename(columns={
        "srn": "SRN", "name": "Name", "submitted_link": "Submitted Link",
        "scrape_status": "Status", "failure_reason": "Reason", "submitted_at": "Submitted At",
    }),
    use_container_width=True, hide_index=True,
)

st.download_button(
    "⬇ Download Failed URLs (CSV)",
    view.to_csv(index=False).encode("utf-8"),
    file_name="failed_scrape_records.csv",
    mime="text/csv",
)
