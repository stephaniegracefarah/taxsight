# taxsight

AI-powered global tax obligation intelligence for digital platforms.

**Status: Phase 1 in progress.**

taxsight builds a structured, source-cited dataset of the tax obligations that apply to digital platforms and marketplaces. It uses the Claude API to extract obligations from public regulatory sources, writes the results to versioned seed CSVs, and models them in dbt on DuckDB.

---

## The problem

A marketplace that operates in several countries picks up obligations from several unrelated regimes at once: seller reporting rules, digital services taxes, US state marketplace facilitator laws, and VAT/GST rules that make the platform the deemed supplier. Each regime is set by a different authority, published in a different format, and changed on its own schedule. The guidance pages themselves move or disappear without notice. Tracking all of this by hand means reading dozens of government and advisory pages and hoping nothing changed since the last time.

---

## What it does today

Phase 1 covers four regimes. Each has its own extraction prompt, build script, and seed CSV. Row counts below are taken from the seed CSVs in `taxsight_dbt/seeds/` (quarter: 2026-Q1).

| Regime | Scope | Seed rows | Source strategy |
|--------|-------|----------:|-----------------|
| Platform reporting | EU DAC7 (27 member states), UK DPI, Canada DPI | 29 | Scrape |
| Digital services taxes | UK, Canada (repealed), and European DSTs tracked by Tax Foundation | 18 | Scrape |
| US marketplace facilitator | 48 jurisdictions (US states plus DC and Puerto Rico) | 48 | Scrape (two guides, merged) |
| VAT/GST marketplace rules | 34 countries | 34 | Research |
| **Total** | | **129** | |

Every row carries the same audit fields: `source_url`, `verbatim_quote` (the source text that supports the extracted values), `confidence_flag` (high / medium / low), and `last_verified_date`.

### Complexity score

Each row has a `complexity_score_base` from 1 to 10. It is computed in the build scripts, not extracted by Claude, from two inputs:

| Input | Rule |
|-------|------|
| Recency (`effective_date`) | 2022 or later → 10 · 2019–2021 → 7 · 2015–2018 → 4 · before 2015 → 2 · unknown → 5 |
| Guidance maturity (`guidance_maturity`) | nascent → +1 · developing → 0 · mature → −1 |

The result is clamped to 1–10. Newer rules and rules with less mature guidance score higher. The dbt schema describes this as the base score "before revenue weighting".

> TODO (Stephanie): confirm how revenue weighting will be applied on top of the base score, and whether to describe it here or in the roadmap.

### End goal

> TODO (Stephanie): describe what a user will be able to do with taxsight when it's finished.

---

## Architecture

```
Public regulatory sources
  ├── EU Commission, HMRC / GOV.UK, CRA / Canada.ca      (government pages)
  ├── Tax Foundation                                    (DST tracker)
  ├── Avalara state guides                              (marketplace facilitator, economic nexus)
  └── Claude web search                                 (VAT/GST, finds and cites its own sources)
          │
          ▼
scripts/etl/etl_extractor.py
  ├── fetch_source()             ← requests + BeautifulSoup, strips nav/script/style
  ├── run_extraction()           ← "scrape" mode: page text + prompt → Claude → JSON
  └── run_research_extraction()  ← "research" mode: Claude + web_search tool → JSON
          │
          │   prompts/etl/*_extraction_v1.txt   (one versioned prompt per regime/source)
          ▼
scripts/etl/extract_*.py, research_vat_gst.py
          │
          ▼
data/raw_extractions/2026-Q1/*.json    ← raw Claude output, committed for auditability
          │
          ▼
scripts/etl/build_*_seed.py
  ├── normalize fields and defaults
  ├── build obligation_id
  ├── compute complexity_score_base
  └── merge_thresholds()          ← marketplace facilitator only
          │
          ▼
taxsight_dbt/seeds/{regime}/{regime}.csv
          │
          ▼
dbt (DuckDB)
  └── models/staging/stg_platform_reporting   ← typed and tested
```

Only the platform reporting regime has a staging model and dbt tests so far. The other three regimes are loaded as seeds.

### Project structure

```
taxsight/
├── data/raw_extractions/2026-Q1/   # raw JSON from each Claude extraction
├── docs/changelog.md               # build log, decisions, lessons learned
├── prompts/etl/                    # extraction prompts, versioned (_v1)
├── scripts/etl/
│   ├── etl_extractor.py            # shared fetch / extract / save helpers
│   ├── extract_dac7.py             # platform reporting: EU
│   ├── extract_uk_dpi.py           # platform reporting: UK
│   ├── extract_ca_dpi.py           # platform reporting: Canada
│   ├── extract_dst.py              # digital services taxes
│   ├── extract_marketplace_fac.py  # US marketplace facilitator (4 passes)
│   ├── research_vat_gst.py         # VAT/GST, research mode (current)
│   ├── extract_vat_gst.py          # VAT/GST, original scrape attempt (superseded)
│   └── build_*_seed.py             # raw JSON → seed CSV, one per regime
└── taxsight_dbt/
    ├── models/staging/             # stg_platform_reporting + schema tests
    └── seeds/                      # one folder per regime
```

---

## Key design decisions

**Two ETL strategies: scrape and research**

Phase 1 ended up with two ways of getting data out of the world and into JSON.

*Scrape mode* fetches one authoritative page, strips it to text, and passes it to Claude with a regime-specific prompt. The prompt tells Claude to extract only what is explicitly stated, return null for anything missing, and include a verbatim quote. This is used when a single authoritative source exists and the page can be fetched: DAC7 (EU Commission), UK DPI (HMRC), Canada DPI (CRA), DSTs (Tax Foundation, GOV.UK, Canada.ca), and marketplace facilitator rules (Avalara state guides).

*Research mode* gives Claude a country, a prompt, and the web search tool (capped at two searches per country). Claude finds its own sources, cites them in `source_url`, and sets `confidence_flag` based on what it found. This is used for VAT/GST marketplace rules, where the information is fragmented across 34 national tax authorities, some government pages block scrapers, and no single source covers marketplace-specific deemed supplier rules.

Scrape mode is preferred whenever it works, because the source is fixed and the output is easier to verify. Research mode trades some of that control for coverage.

**`complexity_score_base` is computed, not extracted**

The score is a taxsight methodology choice, not a fact that appears in any source. Asking Claude to extract it contradicted the extraction rule "never infer values not in the source", and produced values with no traceable basis. It is now computed deterministically in each build script from `effective_date` and `guidance_maturity`, so the same inputs always produce the same score and the rule is the same across all four regimes.

**Two sources for marketplace facilitator thresholds**

The Avalara marketplace facilitator guide is the primary source for facilitator-specific fields. The Avalara economic nexus guide is a secondary source for revenue and transaction thresholds. `merge_thresholds()` in `build_marketplace_fac_seed.py` fills missing thresholds from the secondary source, but where the primary source says there is no facilitator threshold and the nexus guide shows a remote seller threshold, it leaves the threshold null and writes a verification note instead of assuming the two are the same.

**Raw extractions are committed**

Every Claude response is saved as JSON under `data/raw_extractions/{quarter}/` before any transformation. The seed CSVs can be rebuilt from these files without calling the API, and any value in a seed can be traced back to the model output it came from.

---

## What didn't work the first time

**The source URLs were already dead.** All three original URLs for DAC7, UK DPI, and Canada DPI returned 404 during the Phase 1 build. I found the current pages by hand and updated the scripts. Government pages move without redirects, so URL validation is now a manual step in the quarterly refresh checklist, and it is listed as a limitation below.

**Avalara's VAT pages loaded but didn't have the data.** The first VAT/GST attempt (`extract_vat_gst.py`) scraped Avalara VATlive country guides for 34 countries. The pages fetched fine, but they cover general VAT rules, not the marketplace deemed supplier rules taxsight needs, so the extractions came back sparse. I deleted the raw extractions and switched to research mode (`research_vat_gst.py`), with Quaderno, Avalara, and VATCalc as suggested starting points, and let Claude find and cite the country-specific sources.

**I asked Claude to extract a number that should have been computed.** The first versions of the DST, marketplace facilitator, and VAT/GST prompts asked Claude for `complexity_score_base`. That is a derived score, so there was nothing in the source to extract. The platform reporting build script had a different problem: it hardcoded a score of 8 based on revenue proximity, which was the wrong dimension entirely. I removed the field from all prompts, added `compute_complexity_score_base()` to all four build scripts, and rebuilt all 129 seed rows.

**One source wasn't enough for US thresholds.** The Avalara marketplace facilitator guide doesn't state revenue thresholds for eight jurisdictions (CO, HI, IA, MD, NJ, PR, TX, DC). Adding the economic nexus guide as a second source filled in Iowa ($100,000). The other seven keep a null facilitator threshold, with the nexus threshold recorded in `notes` and flagged for verification. Texas, for example, correctly shows its $500,000 nexus threshold, not $100,000.

---

## Data sources and licensing

taxsight is a non-commercial personal project, and sources are reviewed for licensing before use.

| Source | Used for | License / terms | Attribution |
|--------|----------|-----------------|-------------|
| European Commission | Platform reporting: EU DAC7 | CC BY 4.0 | Source credited; changes indicated (content is extracted and restructured into seed rows) |
| HMRC / GOV.UK | Platform reporting: UK DPI; UK DST | Open Government Licence v3.0 | Contains public sector information licensed under the Open Government Licence v3.0. |
| Canada Revenue Agency / Canada.ca | Platform reporting: Canada DPI; Canada DST | Non-commercial reproduction permitted with title, author, and source URL; commercial redistribution requires permission | Title, author, and source URL retained per row in `source_url` |
| Tax Foundation | Digital services taxes (Europe) | CC BY-NC 4.0 | Non-commercial use with attribution: Tax Foundation, source URL retained per row |
| Avalara guides | US marketplace facilitator and economic nexus | Being replaced with primary state department of revenue sources to ensure clear licensing and authoritative data. | — |
| Sources found by Claude web search | VAT/GST marketplace rules (34 countries) | Varies by source; cited per row in `source_url` | TODO (Stephanie): review licensing for research-mode sources. Current seed cites fonoa.com, vatcalc.com, avalara.com, and several national tax authorities, among others. |

---

## Limitations

- **Source URL stability.** Extraction scripts assume source URLs stay stable. Government and regulatory pages move without notice (all three original DAC7, UK, and Canada URLs returned 404 during the Phase 1 build). The quarterly refresh checklist includes URL validation as a manual step.
- **Regulatory scope assumptions.** Scripts assume country-regime applicability doesn't change between quarterly refreshes. Real-world changes (for example, the UK leaving the EU and implementing its own DPI rules instead of DAC7) require manual review and seed CSV updates. taxsight is a point-in-time snapshot, not a real-time monitor.
- **Country classification.** ISO3 codes and country-regime mappings reflect the regulatory landscape as of each row's `last_verified_date`. Political or regulatory changes between refreshes are not detected automatically.
- **v1 scope.** Real-time rule updates, filing preparation, and private company data are out of scope for v1.

taxsight output is not tax or legal advice.

---

## Roadmap

**Phase 1 (in progress)**

- Replace the Avalara marketplace facilitator and economic nexus sources with primary state department of revenue sources
- Add staging models and dbt tests for DST, marketplace facilitator, and VAT/GST (only platform reporting has them today)
- Hero tickers selected for Phase 1 after a geographic segment disclosure check: ETSY, ABNB, SPOT, EBAY, FVRR
- TODO (Stephanie): describe how the hero tickers connect to the obligation dataset, and list any other remaining Phase 1 work

**Later phases**

- TODO (Stephanie): the changelog and code reference a technical design doc (TDD Decision 4, TDD Section 10) that is not in this repo. Add later-phase plans from the TDD here, or link to the TDD if it will be published.

---

## Quick start

**Prerequisites:** Python 3 (TODO (Stephanie): confirm minimum version), git, and an Anthropic API key if you want to re-run extractions.

```bash
# Clone and set up environment
git clone https://github.com/stephaniegracefarah/taxsight.git
cd taxsight
python -m venv venv
source venv/bin/activate
pip install anthropic requests beautifulsoup4 python-dotenv dbt-duckdb
# TODO (Stephanie): add a requirements.txt with pinned versions (dbt 1.11 was used)

# Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env (only needed for extraction)
```

**Optional: re-run extractions.** These call the Claude API and overwrite the files in `data/raw_extractions/2026-Q1/`. Skip this step to build from the committed raw extractions.

```bash
python scripts/etl/extract_dac7.py
python scripts/etl/extract_uk_dpi.py
python scripts/etl/extract_ca_dpi.py
python scripts/etl/extract_dst.py
python scripts/etl/extract_marketplace_fac.py   # 4 passes: 2 guides × 2 state ranges
python scripts/etl/research_vat_gst.py          # skips countries already extracted; waits 45s between calls for rate limits
```

**Build seed CSVs** (no API key needed):

```bash
python scripts/etl/build_platform_reporting_seed.py
python scripts/etl/build_dst_seed.py
python scripts/etl/build_marketplace_fac_seed.py
python scripts/etl/build_vat_gst_seed.py
```

**Load and test in dbt.** The project uses a `taxsight_dbt` profile, which is not committed. A minimal DuckDB profile in `~/.dbt/profiles.yml`:

```yaml
taxsight_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: dev.duckdb   # TODO (Stephanie): confirm the database path you use
```

```bash
cd taxsight_dbt
dbt build    # loads seeds, builds stg_platform_reporting, runs schema tests
```

---

## Stack

Python · Anthropic Claude API (Claude Sonnet, web search tool) · requests · BeautifulSoup · dbt Core · DuckDB
