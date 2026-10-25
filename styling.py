"""Shared CSS injection and small UI helper components."""

from __future__ import annotations

import streamlit as st

from src import config


def inject_global_css() -> None:
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap" rel="stylesheet">
        <style>
            html, body, [class*="css"] {{
                font-family: 'Inter', sans-serif;
            }}
            .block-container {{
                padding-top: 1.6rem;
                padding-bottom: 3rem;
                max-width: 1300px;
            }}
            #MainMenu, footer {{visibility: hidden;}}

            h1, h2, h3 {{
                font-family: 'Poppins', sans-serif;
                font-weight: 700;
                color: {config.COLOR_TEXT};
            }}

            /* Hero */
            .hero {{
                background: linear-gradient(rgba(11,31,58,.88), rgba(11,31,58,.88));
                border-radius: 24px;
                padding: 4rem 3rem;
                color: white;
                margin-bottom: 2rem;
                box-shadow: 0 15px 40px rgba(0,0,0,.20);
                border-left: 6px solid #F58220;
            }}
            .hero h1 {{
                color: white;
                font-size: 3rem;
                font-weight: 800;
            }}
            .hero p {{
                color: #E5E7EB;
                font-size: 1.1rem;
            }}
            .hero .badge {{
                display: inline-block;
                background: #F58220;
                color: white;
                border: none;
                padding: .4rem 1rem;
                border-radius: 30px;
                font-weight: 700;
                margin-bottom: 18px;
            }}

            /* KPI cards */
            .kpi-card {{
                background: white;
                border-radius: 18px;
                padding: 1.4rem;
                border-top: 5px solid #F58220;
                box-shadow: 0 8px 24px rgba(0,0,0,.08);
                transition: .25s;
            }}
            .kpi-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 16px 30px rgba(0,0,0,.15);
            }}
            .kpi-label {{
                color: #64748B;
                font-size: .8rem;
                text-transform: uppercase;
                font-weight: 700;
            }}
            .kpi-value {{
                color: #0B1F3A;
                font-size: 2rem;
                font-weight: 800;
            }}
            .kpi-sub {{
                color: #6B7280;
            }}

            /* Section card wrapper */
            .card {{
                background: white;
                border-radius: 18px;
                padding: 1.6rem;
                box-shadow: 0 8px 24px rgba(0,0,0,.08);
                border-top: 5px solid #F58220;
            }}

            .pill {{
                display: inline-block;
                background: {config.COLOR_BG};
                border: 1px solid rgba(31,27,30,0.08);
                border-radius: 999px;
                padding: 0.15rem 0.65rem;
                font-size: 0.72rem;
                margin: 0.12rem;
                color: {config.COLOR_TEXT};
            }}

            .status-ok {{ color: {config.COLOR_SUCCESS}; font-weight: 700; }}
            .status-bad {{ color: {config.COLOR_DANGER}; font-weight: 700; }}

            /* Streamlit Component Overrides */
            div[data-testid="stMetric"] {{
                background: white;
                border-radius: 16px;
                padding: 1rem;
                border-left: 5px solid #F58220;
                box-shadow: 0 6px 18px rgba(0,0,0,.08);
            }}

            section[data-testid="stSidebar"] {{
                background: #0B1F3A;
            }}

            section[data-testid="stSidebar"] * {{
                color: white;
            }}

            .stButton>button {{
                background: #F58220;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: 700;
                padding: .7rem 1.5rem;
            }}

            .stButton>button:hover {{
                background: #0B1F3A;
                color: white;
            }}

            .stApp {{
                background: #F5F7FA;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, sub: str = "") -> str:
    return f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
    """


def render_kpi_row(items: list[tuple[str, str, str]], cols_per_row: int = 4) -> None:
    """items: list of (label, value, sub)."""
    for i in range(0, len(items), cols_per_row):
        row_items = items[i : i + cols_per_row]
        cols = st.columns(len(row_items))
        for col, (label, value, sub) in zip(cols, row_items):
            with col:
                st.markdown(kpi_card(label, value, sub), unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.write("")