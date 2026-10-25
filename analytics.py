"""
Analytics layer - every number and aggregation shown in the UI is computed
here and cached, so pages only call functions and render results.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from src import config
from src.data_pipeline import load_everything


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner="Loading alumni data...")
def get_data(_fingerprint: tuple):
    """The `_fingerprint` argument (file mtimes+sizes) is the real cache
    key: Streamlit hashes it, and it changes automatically the moment a
    new file is dropped into data/raw/, which invalidates the cache and
    triggers a fresh load/clean/merge - this is the "automatic update"
    mechanism described in the README."""
    profiles, submissions, master, sources = load_everything()
    return profiles, submissions, master


def load_all():
    from src.data_pipeline import discover_source_files
    sources = discover_source_files()
    return get_data(sources.fingerprint)


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
def compute_kpis(profiles: pd.DataFrame, submissions: pd.DataFrame, master: pd.DataFrame) -> dict:
    total_submitted = len(submissions)
    total_scraped = len(profiles)
    total_failed = master["scrape_status"].str.startswith("Failed").sum()
    success_rate = (total_scraped / total_submitted * 100) if total_submitted else 0.0

    real_companies = profiles.loc[~profiles["is_self_reference"], "company_clean"].dropna()
    self_ref = profiles["is_self_reference"].sum()
    unknown_company = profiles["company_clean"].isna().sum()

    return {
        "total_submitted": total_submitted,
        "total_scraped": total_scraped,
        "total_failed": int(total_failed),
        "success_rate": round(success_rate, 1),
        "profiles_with_company_signal": int(len(real_companies)),
        "profiles_self_reference_only": int(self_ref),
        "profiles_no_company_listed": int(unknown_company),
        "unique_companies": int(real_companies.nunique()),
        "unique_locations": int(profiles["location"].dropna().nunique()),
        "avg_connections": round(profiles["connections"].dropna().mean() or 0, 0),
        "avg_followers": round(profiles["followers"].dropna().mean() or 0, 0),
        "profiles_with_skills": int((profiles["skill_count"] > 0).sum()),
        "avg_alumni_per_company": round(
            real_companies.value_counts().mean() if not real_companies.empty else 0, 1
        ),
    }


# ---------------------------------------------------------------------------
# Company analytics
# ---------------------------------------------------------------------------
def top_companies(profiles: pd.DataFrame, n: int = 20, exclude_self: bool = True) -> pd.DataFrame:
    df = profiles.copy()
    if exclude_self:
        df = df[~df["is_self_reference"]]
    counts = (
        df["company_clean"].dropna().value_counts().head(n).rename_axis("company").reset_index(name="count")
    )
    return counts


def company_detail(profiles: pd.DataFrame, company: str) -> pd.DataFrame:
    return profiles[profiles["company_clean"] == company][
        ["name", "headline", "location", "linkedin_url", "connections", "followers"]
    ].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Skills analytics
# ---------------------------------------------------------------------------
def top_skills(profiles: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    exploded = profiles.explode("skills")
    exploded = exploded[exploded["skills"].notna()]
    counts = exploded["skills"].value_counts().head(n).rename_axis("skill").reset_index(name="count")
    return counts


# ---------------------------------------------------------------------------
# Scraping / data-quality analytics
# ---------------------------------------------------------------------------
def scraping_funnel(master: pd.DataFrame) -> pd.DataFrame:
    counts = master["scrape_status"].value_counts().rename_axis("status").reset_index(name="count")
    return counts


def failure_breakdown(master: pd.DataFrame) -> pd.DataFrame:
    failed = master[master["scrape_status"].str.startswith("Failed")]
    counts = failed["failure_reason"].value_counts().rename_axis("reason").reset_index(name="count")
    return counts


def failed_records(master: pd.DataFrame) -> pd.DataFrame:
    failed = master[master["scrape_status"].str.startswith("Failed")]
    cols = [c for c in ["srn", "name", "submitted_link", "scrape_status", "failure_reason", "submitted_at"] if c in failed.columns]
    return failed[cols].sort_values("srn").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Directory search / filter
# ---------------------------------------------------------------------------
def search_profiles(
    profiles: pd.DataFrame,
    query: str = "",
    companies: Optional[list[str]] = None,
    min_connections: Optional[int] = None,
    has_skills_only: bool = False,
) -> pd.DataFrame:
    df = profiles.copy()
    if query:
        q = query.lower().strip()
        mask = (
            df["name"].fillna("").str.lower().str.contains(q)
            | df["company"].fillna("").str.lower().str.contains(q)
            | df["headline"].fillna("").str.lower().str.contains(q)
            | df["location"].fillna("").str.lower().str.contains(q)
            | df["srn"].fillna("").str.lower().str.contains(q)
            | df["skills"].map(lambda s: any(q in sk.lower() for sk in s) if s else False)
        )
        df = df[mask]
    if companies:
        df = df[df["company_clean"].isin(companies)]
    if min_connections:
        df = df[df["connections"].fillna(0) >= min_connections]
    if has_skills_only:
        df = df[df["skill_count"] > 0]
    return df.reset_index(drop=True)
