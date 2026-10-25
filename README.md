# PES University Alumni Intelligence Platform

A Streamlit analytics application built on the Class of 2026 LinkedIn
collection drive: a Google Form of submitted profile links plus a scraper's
output for the profiles it could reach.

## ⚠️ Read this first: what the data actually supports

Before anything else, an honest note on scope. The three source files are:

| File | What it is |
|---|---|
| `Class_of_2026-LinkedIn_Profiles_copy.xlsx` | 816 raw Google Form submissions (737 unique SRNs) — every link a student submitted, including junk (`Na`, `linkedin.com/me`, duplicates). |
| `alumni_cleaned.xlsx` / `alumni_cleaned.json` | 510 rows (470 unique SRNs) of **scraped profile data** for the submissions that could be processed. The JSON version has `skills` as a real list; the XLSX has it as a comma string — the pipeline normalizes both. |

Because this is the **graduating class of 2026**, not alumni several years
out, almost every `Headline` reads *"Student at PES University"* and every
`Location` is Bengaluru. There is no reliable "pursuing Master's at X
University" field, and no confirmed "working professional vs. higher
studies" signal beyond a handful of free-text mentions in `About`. So this
build deliberately does **not** fabricate those categories. Instead it
reports:

- **Scraping funnel health** — submitted → scraped → failed, and why.
- **Employer/internship signal** from the `Company` field, with self-referencing
  "PES University" entries (not-yet-updated profiles) separated out rather
  than counted as an employer.
- **Skills, connections, followers** — the fields that are genuinely populated.

If PES later collects real alumni-years-out data (confirmed employer,
postgrad university, start/end dates), the `src/data_pipeline.py` and
`src/analytics.py` modules are the only places that need new fields —
every page already reads from those two modules, not from raw files.

## Architecture

```
pes-alumni-platform/
├── app.py                     # Landing page (hero, KPIs, quick nav)
├── pages/
│   ├── 1_Dashboard.py         # Executive KPI dashboard
│   ├── 2_Alumni_Directory.py  # Search / filter / sort / export
│   ├── 3_Company_Analytics.py # Rankings, treemap, sunburst, drill-down
│   ├── 4_Skills_Analytics.py  # Skill frequency + profile lookup
│   └── 5_Data_Quality.py      # Scraping funnel + failed-record export
├── src/
│   ├── config.py               # Paths, brand colors, constants — nothing
│   │                            #   hardcoded elsewhere
│   ├── data_pipeline.py        # Load, clean, normalize, dedupe, merge
│   ├── analytics.py            # Cached KPI/aggregation functions
│   └── styling.py               # Shared CSS + small UI components
├── data/
│   ├── raw/                    # Source files (see "Updating Data" below)
│   └── processed/              # Reserved for future materialized caches
├── .streamlit/config.toml      # Native theme (colors match src/config.py)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

**Why this split:** `data_pipeline.py` is the only module that touches raw
Excel/JSON. `analytics.py` is the only module that computes metrics, and
wraps loading in `st.cache_data` keyed on file mtimes/sizes — so the cache
invalidates itself the moment a source file changes. Every page under
`pages/` only calls into `analytics.py` and `styling.py`; there is no
business logic inside a page file, per standard separation-of-concerns
practice for data apps.

## Installation

```bash
git clone <your-repo-url>
cd pes-alumni-platform
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running locally

```bash
streamlit run app.py
```

Visit `http://localhost:8501`.

## Updating data (no code changes required)

1. Drop a new profiles export into `data/raw/` named `alumni_cleaned.json`
   or `alumni_cleaned.xlsx` (JSON is preferred — it preserves `skills` as a
   proper list).
2. Drop a new submissions export into `data/raw/` matching
   `*LinkedIn_Profiles*.xlsx`.
3. Reload the app (or wait for the cache TTL — default 1 hour, controlled by
   `PESU_CACHE_TTL`). `src/data_pipeline.py::discover_source_files()` picks
   the newest matching file automatically and `src/analytics.py` uses its
   mtime+size as the Streamlit cache key, so a new file always forces a
   fresh load → clean → merge pass.

Nothing in `data/raw/` is ever modified in place — cleaning and merging
happen in memory on every cache-invalidated load.

## Configuration

All tunables are environment variables, read in `src/config.py`:

| Variable | Default | Purpose |
|---|---|---|
| `PESU_CACHE_TTL` | `3600` | Seconds before Streamlit re-checks source files |
| `PESU_DEBUG` | `false` | Reserved for verbose logging |

## Deployment

### Streamlit Community Cloud
Push this repo to GitHub, then on [share.streamlit.io](https://share.streamlit.io)
point to `app.py` as the main file. No secrets required for the current
dataset (it ships in `data/raw/`).

### Docker
```bash
docker build -t pesu-alumni-platform .
docker run -p 8501:8501 pesu-alumni-platform
```

### Docker Compose
```bash
docker compose up --build
```

### Render / Google Cloud Run
Both platforms build directly from the included `Dockerfile`. Set the
service port to `8501` and, if the platform requires it, a `PORT` env var
mapped to `--server.port` in the Streamlit start command.

## Known limitations / next steps

- **No PDF report export yet** — CSV/Excel export is implemented on the
  Directory and Data Quality pages; PDF generation is a reasonable next
  addition (e.g. via `reportlab`) once report layout is agreed with the
  university.
- **No authentication** — this is read-only public analytics over
  already-public LinkedIn fields. Add an auth layer before including any
  non-public data.
- **Company name normalization is heuristic** (case/whitespace + a fixed
  list of "this is really PES University" aliases). A larger dataset would
  benefit from a maintained alias table in `src/config.py`.
- **Photos are not scraped** in the current dataset, so the directory shows
  initials/placeholder rather than real photos.
- Performance has been validated for the current ~500–800 row scale.
  `st.cache_data` and vectorized pandas operations should comfortably carry
  this to low tens of thousands of rows; a true 100k+-row deployment would
  warrant moving from in-memory pandas to a real database (Postgres/DuckDB)
  behind `src/data_pipeline.py` — the module boundary is already set up for
  that swap.

## Troubleshooting

- **"Could not find both a profiles file and a submissions file"** — check
  `data/raw/` contains a file matching `alumni_cleaned.json`/`.xlsx` and one
  matching `*LinkedIn_Profiles*.xlsx`.
- **Stale numbers after replacing a file** — confirm the new file's name
  matches the patterns above; a differently-named file won't be discovered.
