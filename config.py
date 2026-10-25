"""
Central configuration for the PES Alumni Intelligence Platform.

Every path, color, and tunable constant lives here so nothing is
hardcoded inside page files or business logic. Paths are resolved
relative to the project root (not the current working directory),
so the app behaves the same whether it's launched from the repo
root, a Docker container, or Streamlit Cloud.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ASSETS_DIR = ROOT_DIR / "assets"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Source files. New files matching these patterns are auto-picked-up by
# src/data_pipeline.py::discover_source_files() -- see that module for the
# "drop a file in data/raw and it gets merged in" behavior.
PROFILE_FILE_CANDIDATES = ["alumni_cleaned.json", "alumni_cleaned.xlsx"]
SUBMISSION_FILE_GLOB = "*LinkedIn_Profiles*.xlsx"

# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
APP_TITLE = "PES University Alumni Intelligence Platform"
APP_SHORT_TITLE = "PESU Alumni Intelligence"
ORG_NAME = "PES University"

# PES University's identity is built around a deep crimson/maroon with a
# gold accent. These are used consistently across every chart and every
# injected CSS block in src/styling.py so the whole app reads as one
# product rather than a stack of default-themed pages.
COLOR_PRIMARY = "#0B1F3A"  # Dark Blue
COLOR_ACCENT = "#F58220"   # Orange Accent
# Keep your other configuration variables below...
COLOR_SECONDARY = "#F58220"       # Orange
COLOR_BG = "#F5F7FA"              # Light Gray
COLOR_SURFACE = "#FFFFFF"         # White
COLOR_TEXT = "#0B1F3A"            # Navy Text
COLOR_MUTED = "#6B7280"
COLOR_SUCCESS = "#22C55E"
COLOR_DANGER = "#EF4444"

CHART_PALETTE = [
    "#0B1F3A",
    "#F58220",
    "#1D4ED8",
    "#FBBF24",
    "#64748B",
]

# ---------------------------------------------------------------------------
# Data-quality / classification constants
# ---------------------------------------------------------------------------
# LinkedIn "self" / placeholder / not-yet-updated links captured by the
# scraper as junk rather than a real profile. Anything matching these is
# flagged as an invalid submission rather than a "failed scrape".
INVALID_LINK_PATTERNS = [
    r"^na$", r"^n/a$", r"^-+$", r"^\s*$",
    r"linkedin\.com/me\b", r"linkedin\.com/feed/?$", r"linkedin\.com/?$",
    r"linkedin\.com/mwlite",
]

# Company-name spelling/casing variants that all refer to the university
# itself (a placeholder headline rather than a real employer). Grouped so
# analytics can separate "hasn't updated their profile yet" from actual
# employment/internship signal.
SELF_ORG_ALIASES = [
    "pes university", "pesu", "pes univeristy", "pes university 2026",
    "pes innovation lab",
]

# Environment overrides (useful in Docker / Render / Cloud Run where you
# don't want to bake paths or secrets into the image).
DEBUG = os.getenv("PESU_DEBUG", "false").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("PESU_CACHE_TTL", "3600"))
