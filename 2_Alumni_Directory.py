from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src import config
from src.analytics import load_all, search_profiles
from src.styling import inject_global_css, page_header

st.set_page_config(page_title="Directory · " + config.APP_SHORT_TITLE, page_icon="👥", layout="wide")
inject_global_css()

profiles, submissions, master = load_all()

page_header("Alumni Directory", "Search and filter the full class list. Filters apply instantly.")

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 1.3, 1, 1])
    with c1:
        query = st.text_input("Search", placeholder="Name, company, skill, location, SRN...", label_visibility="collapsed")
    with c2:
        company_options = sorted(profiles.loc[~profiles["is_self_reference"], "company_clean"].dropna().unique().tolist())
        companies = st.multiselect("Company", company_options, label_visibility="collapsed", placeholder="Filter by company")
    with c3:
        min_conn = st.number_input("Min connections", min_value=0, value=0, step=10, label_visibility="collapsed")
    with c4:
        skills_only = st.checkbox("Has skills listed")
    st.markdown("</div>", unsafe_allow_html=True)

results = search_profiles(
    profiles, query=query, companies=companies or None,
    min_connections=min_conn or None, has_skills_only=skills_only,
)

st.write(f"**{len(results):,}** of {len(profiles):,} profiles match")

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
export_cols = ["name", "srn", "company", "headline", "location", "skills",
               "connections", "followers", "linkedin_url"]
export_df = results[export_cols].copy()
export_df["skills"] = export_df["skills"].map(lambda s: ", ".join(s) if s else "")

ec1, ec2, _ = st.columns([1, 1, 4])
with ec1:
    st.download_button(
        "⬇ Export CSV", export_df.to_csv(index=False).encode("utf-8"),
        file_name="alumni_directory_export.csv", mime="text/csv", use_container_width=True,
    )
with ec2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Alumni Directory")
    st.download_button(
        "⬇ Export Excel", buf.getvalue(), file_name="alumni_directory_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
    )

st.write("")

# ---------------------------------------------------------------------------
# Sort + paginate
# ---------------------------------------------------------------------------
sort_col, page_col = st.columns([1, 3])
with sort_col:
    sort_by = st.selectbox("Sort by", ["name", "connections", "followers", "company_clean"], format_func=str.title)
results = results.sort_values(sort_by, ascending=(sort_by == "name"), na_position="last")

PAGE_SIZE = 20
total_pages = max(1, (len(results) - 1) // PAGE_SIZE + 1)
with page_col:
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

page_df = results.iloc[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

for _, row in page_df.iterrows():
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2.5, 2, 1.2])
        with c1:
            st.markdown(f"**{row['name'] or 'Unknown'}**  \n`{row['srn'] or '—'}`")
            st.caption(row["headline"] or "—")
        with c2:
            st.write(f"🏢 {row['company_clean'] or '—'}")
            st.write(f"📍 {row['location'] or '—'}")
        with c3:
            import pandas as pd

            connections = 0 if pd.isna(row["connections"]) else int(row["connections"])
            st.write(f"🔗 {connections} connections")
            followers = int(row["followers"]) if pd.notna(row["followers"]) else 0
            st.write(f"👁️ {followers} followers")
            if row["linkedin_url"]:
                st.markdown(f"[View LinkedIn ↗]({row['linkedin_url']})")
        if row["skills"]:
            st.markdown(
                "".join(f'<span class="pill">{s}</span>' for s in row["skills"][:12]),
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"Page {page} of {total_pages}")
