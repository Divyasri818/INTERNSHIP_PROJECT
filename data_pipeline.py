"""
Data loading, cleaning, deduplication, and merging.

Design notes
------------
This dataset is the "Class of 2026" LinkedIn collection drive: a Google
Form of submitted profile links (the *submissions* file) and a scraper's
output for the links it could successfully process (the *profiles*
file/JSON). It is NOT a multi-year alumni database with employment
history or postgrad-university fields - nearly every headline reads
"Student at PES University" because these are graduating students, not
alumni years out. The pipeline below is honest about that: it reports
scraping funnel health (submitted -> scraped -> failed) and whatever
real signal exists in the Company/About/Skills fields, rather than
inventing categories the data can't support.

Auto-update behavior
---------------------
`discover_source_files()` re-scans data/raw/ on every call (Streamlit's
cache is keyed on file mtimes, see @st.cache_data(hash_funcs=...) usage
in load_master_dataset). Drop a new profiles JSON/XLSX or a new
submissions XLSX into data/raw/ with a matching filename pattern
(see config.PROFILE_FILE_CANDIDATES / SUBMISSION_FILE_GLOB) and the next
page load picks it up automatically - no code changes needed.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from src import config

logger = logging.getLogger("pesu_alumni.data_pipeline")
logging.basicConfig(level=logging.INFO)

_INVALID_LINK_RE = re.compile("|".join(config.INVALID_LINK_PATTERNS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# File discovery (enables the "drop a file, it updates" workflow)
# ---------------------------------------------------------------------------
@dataclass
class SourceFiles:
    profiles_path: Optional[Path]
    submissions_path: Optional[Path]
    fingerprint: tuple  # (mtime, size) pairs -> used as a cache key


def discover_source_files() -> SourceFiles:
    """Find the newest matching profile and submission files in data/raw."""
    profiles_path = None
    for name in config.PROFILE_FILE_CANDIDATES:
        candidate = config.RAW_DATA_DIR / name
        if candidate.exists():
            profiles_path = candidate
            break

    submission_matches = sorted(config.RAW_DATA_DIR.glob(config.SUBMISSION_FILE_GLOB))
    submissions_path = submission_matches[-1] if submission_matches else None

    fp = []
    for p in (profiles_path, submissions_path):
        if p and p.exists():
            stat = p.stat()
            fp.append((str(p), stat.st_mtime, stat.st_size))
    return SourceFiles(profiles_path, submissions_path, tuple(fp))


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------
def _clean_str(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "na", "n/a"}:
        return None
    return " ".join(text.split())


def normalize_company(raw: Optional[str]) -> tuple[Optional[str], bool]:
    """Return (clean_company_name, is_self_reference_to_the_university)."""
    text = _clean_str(raw)
    if text is None:
        return None, False
    lowered = text.lower()
    if lowered in config.SELF_ORG_ALIASES or "pes univer" in lowered or lowered == "pesu":
        return "PES University", True
    return text, False


def is_invalid_link(raw: Optional[str]) -> bool:
    text = _clean_str(raw)
    if text is None:
        return True
    return bool(_INVALID_LINK_RE.search(text.lower()))


_SKILL_UI_NOISE = {
    "post", "posts", "featured", "link", "links", "media", "activity",
    "comment", "comments", "reaction", "reactions", "certificate",
}


def _parse_skills(value) -> list[str]:
    """Skills arrive as a real list in the JSON export and as a
    comma/semicolon-joined string in the XLSX export; both can also
    contain bullet-joined sub-lists or scraper noise (LinkedIn UI labels
    or whole activity-feed captions mistakenly captured as "skills").
    Normalize all of it into a clean, deduplicated list of plausible
    skill tokens rather than presenting scraper noise as real skills."""
    if isinstance(value, list):
        raw_items = [str(v) for v in value if _clean_str(v)]
    else:
        text = _clean_str(value)
        raw_items = [text] if text else []

    tokens: list[str] = []
    for item in raw_items:
        for part in re.split(r"[•|;,]|(?<!\w)/(?!\w)", item):
            part = part.strip(" .\t\n")
            if not part:
                continue
            word_count = len(part.split())
            if word_count > 6 or len(part) > 45:
                continue  # sentence-like text, not a skill token
            if part.lower() in _SKILL_UI_NOISE:
                continue
            tokens.append(part)

    seen, deduped = set(), []
    for t in tokens:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(t)
    return deduped


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_profiles(path: Path) -> pd.DataFrame:
    """Load the scraped-profile dataset from either JSON or XLSX."""
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        df = pd.json_normalize(raw)
        rename = {
            "name": "name", "srn": "srn", "company": "company",
            "linkedin_url": "linkedin_url", "headline": "headline",
            "location": "location", "about": "about", "skills": "skills",
            "stats.connections": "connections", "stats.followers": "followers",
        }
        df = df.rename(columns=rename)
    else:
        df = pd.read_excel(path)
        df = df.rename(columns={
            "Name": "name", "SRN": "srn", "Company": "company",
            "Headline": "headline", "Location": "location", "About": "about",
            "Skills": "skills", "Connections": "connections",
            "Followers": "followers", "LinkedIn URL": "linkedin_url",
        })

    for col in ["name", "srn", "company", "headline", "location", "about", "linkedin_url"]:
        if col not in df.columns:
            df[col] = None
        df[col] = df[col].map(_clean_str)

    if "skills" not in df.columns:
        df["skills"] = [[] for _ in range(len(df))]
    df["skills"] = df["skills"].map(_parse_skills)
    df["skill_count"] = df["skills"].map(len)

    for col in ["connections", "followers"]:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    normalized = df["company"].map(normalize_company)
    df["company_clean"] = normalized.map(lambda t: t[0])
    df["is_self_reference"] = normalized.map(lambda t: t[1])

    df["srn"] = df["srn"].str.upper()
    df = df[df["srn"].notna()].copy()
    # Multiple scrape attempts for the same SRN can exist; keep the richest
    # record (most non-null fields) rather than an arbitrary first row.
    df["_completeness"] = df.notna().sum(axis=1)
    df = (
        df.sort_values("_completeness", ascending=False)
        .drop_duplicates(subset="srn", keep="first")
        .drop(columns="_completeness")
        .reset_index(drop=True)
    )
    df["scrape_status"] = "Scraped"
    return df


def _classify_failure_reason(link: Optional[str]) -> str:
    text = _clean_str(link)
    if text is None:
        return "No link provided"
    if is_invalid_link(text):
        return "Invalid / placeholder link"
    return "Submitted but not scraped (private, timed out, or rate-limited)"


def load_submissions(path: Path) -> pd.DataFrame:
    """Load the raw Google-Form submission log (every link students gave)."""
    df = pd.read_excel(path)
    df = df.rename(columns={
        "Timestamp": "submitted_at", "SRN": "srn", "Name": "name",
        "LinkedIn Profile Link": "submitted_link",
    })
    for col in ["srn", "name", "submitted_link"]:
        df[col] = df[col].map(_clean_str)
    df["srn"] = df["srn"].str.upper()
    df = df[df["srn"].notna()].copy()
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], errors="coerce")
    # Keep the latest submission per SRN (students occasionally resubmitted).
    df = (
        df.sort_values("submitted_at")
        .drop_duplicates(subset="srn", keep="last")
        .reset_index(drop=True)
    )
    df["link_invalid"] = df["submitted_link"].map(is_invalid_link)
    return df


# ---------------------------------------------------------------------------
# Master merge
# ---------------------------------------------------------------------------
def build_master_dataset(profiles: pd.DataFrame, submissions: pd.DataFrame) -> pd.DataFrame:
    """Outer-join submissions with scraped profiles on SRN and derive a
    single `scrape_status` column describing the fate of every submitted
    link: Scraped / Failed - Invalid Link / Failed - Scrape Error."""
    merged = submissions.merge(
        profiles, on="srn", how="outer", suffixes=("_submitted", "")
    )

    merged["name"] = merged["name"].fillna(merged.get("name_submitted"))
    scraped_mask = merged["scrape_status"].eq("Scraped")

    def _status(row) -> str:
        if row["scrape_status"] == "Scraped":
            return "Scraped"
        if bool(row.get("link_invalid")):
            return "Failed - Invalid/Placeholder Link"
        return "Failed - Scrape Error (private/timeout/rate-limit)"

    merged["scrape_status"] = merged.apply(_status, axis=1)
    merged["failure_reason"] = merged["submitted_link"].map(_classify_failure_reason)
    merged.loc[scraped_mask, "failure_reason"] = "N/A - scraped successfully"

    drop_cols = [c for c in merged.columns if c.endswith("_submitted") and c != "name_submitted"]
    merged = merged.drop(columns=drop_cols, errors="ignore")
    return merged


def load_everything() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, SourceFiles]:
    """Convenience entrypoint used by the Streamlit cache wrapper in
    src/analytics.py. Returns (profiles, submissions, master, sources)."""
    sources = discover_source_files()
    if sources.profiles_path is None or sources.submissions_path is None:
        raise FileNotFoundError(
            "Could not find both a profiles file and a submissions file in "
            f"{config.RAW_DATA_DIR}. Expected one of "
            f"{config.PROFILE_FILE_CANDIDATES} and a file matching "
            f"'{config.SUBMISSION_FILE_GLOB}'."
        )
    profiles = load_profiles(sources.profiles_path)
    submissions = load_submissions(sources.submissions_path)
    master = build_master_dataset(profiles, submissions)
    logger.info(
        "Loaded %d profiles, %d submissions, %d master rows",
        len(profiles), len(submissions), len(master),
    )
    return profiles, submissions, master, sources
